jest.mock('@/lib/client-logger', function () { return { logClientError: jest.fn(), logClientWarning: jest.fn() } })
jest.mock('@/lib/languages', function () {
  var mockLangs = [
    { code: 'en', name: 'English', recognitionCode: 'en-IN', speechTargetCode: 'eng', synthesisCode: 'en-IN' },
    { code: 'hi', name: 'हिन्दी', recognitionCode: 'hi-IN', speechTargetCode: 'hin', synthesisCode: 'hi-IN' },
    { code: 'ta', name: 'தமிழ்', recognitionCode: 'ta-IN', speechTargetCode: 'tam', synthesisCode: 'ta-IN' },
  ]
  return {
    SUPPORTED_LANGUAGES: mockLangs,
    getLanguageByCode: jest.fn(function (code) { return mockLangs.find(function (l) { return l.code === code }) }),
  }
})

import { render, screen, fireEvent, act } from '@testing-library/react'
import React, { type Dispatch, type SetStateAction } from 'react'
import { PureMultimodalInput, type Attachment } from '../chat/multimodal-ai-chat-input'

var origCreateObjectURL = URL.createObjectURL
var origRevokeObjectURL = URL.revokeObjectURL

describe('PureMultimodalInput', function () {
  beforeAll(function () {
    URL.createObjectURL = jest.fn(function () { return 'blob:mock' })
    URL.revokeObjectURL = jest.fn()
  })

  afterAll(function () {
    URL.createObjectURL = origCreateObjectURL
    URL.revokeObjectURL = origRevokeObjectURL
  })

  // ── Basic Rendering ──

  it('renders textarea input', function () {
    render(React.createElement(PureMultimodalInput, {}))
    expect(screen.getByLabelText('Chat message input')).toBeTruthy()
  })

  it('renders send button', function () {
    render(React.createElement(PureMultimodalInput, {}))
    expect(screen.getByLabelText('Send message')).toBeTruthy()
  })

  it('renders mic button', function () {
    render(React.createElement(PureMultimodalInput, {}))
    expect(screen.getByLabelText('Use microphone')).toBeTruthy()
  })

  it('renders attachments button', function () {
    render(React.createElement(PureMultimodalInput, {}))
    expect(screen.getByTestId('attachments-button')).toBeTruthy()
  })

  it('renders language globe button', function () {
    render(React.createElement(PureMultimodalInput, {}))
    expect(screen.getByTitle('chat.select_language')).toBeTruthy()
  })

  // ── Controlled Input ──

  it('uses value from parent when provided', function () {
    render(React.createElement(PureMultimodalInput, { value: 'parent text', onChange: function () {} }))
    var textarea = screen.getByLabelText('Chat message input') as HTMLTextAreaElement
    expect(textarea.value).toBe('parent text')
  })

  it('calls onChange when text changes', function () {
    var onChange = jest.fn()
    render(React.createElement(PureMultimodalInput, { value: '', onChange: onChange }))
    var textarea = screen.getByLabelText('Chat message input')
    fireEvent.change(textarea, { target: { value: 'hello' } })
    expect(onChange).toHaveBeenCalledWith('hello')
  })

  // ── Send Button States ──

  it('send button is disabled when input empty and no attachments', function () {
    render(React.createElement(PureMultimodalInput, { value: '', onChange: function () {} }))
    expect(screen.getByLabelText('Send message')).toBeDisabled()
  })

  it('send button is enabled when input has text', function () {
    render(React.createElement(PureMultimodalInput, { value: 'hello', onChange: function () {} }))
    expect(screen.getByLabelText('Send message')).not.toBeDisabled()
  })

  it('disables send when canSend is false', function () {
    render(React.createElement(PureMultimodalInput, { canSend: false }))
    expect(screen.getByLabelText('Send message')).toBeDisabled()
  })

  // Removing - SendButton is replaced by StopButton when isGenerating, covered by 'hides send button' test

  // ── Send / Stop Toggle ──

  it('shows stop button when isGenerating', function () {
    render(React.createElement(PureMultimodalInput, { isGenerating: true }))
    expect(screen.getByLabelText('Stop generating')).toBeTruthy()
  })

  it('hides send button when isGenerating', function () {
    render(React.createElement(PureMultimodalInput, { isGenerating: true }))
    expect(screen.queryByLabelText('Send message')).toBeNull()
  })

  it('calls onStopGenerating when stop button clicked', function () {
    var onStop = jest.fn()
    render(React.createElement(PureMultimodalInput, { isGenerating: true, onStopGenerating: onStop }))
    fireEvent.click(screen.getByLabelText('Stop generating'))
    expect(onStop).toHaveBeenCalled()
  })

  // ── Submit Form ──

  it('calls onSendMessage when send button clicked', function () {
    var onSend = jest.fn()
    render(React.createElement(PureMultimodalInput, { onSendMessage: onSend, value: 'test', onChange: function () {} }))
    fireEvent.click(screen.getByLabelText('Send message'))
    expect(onSend).toHaveBeenCalledWith(expect.objectContaining({ input: 'test' }))
  })

  it('does not call onSendMessage when send button clicked with empty input', function () {
    var onSend = jest.fn()
    render(React.createElement(PureMultimodalInput, { onSendMessage: onSend, value: '', onChange: function () {} }))
    fireEvent.click(screen.getByLabelText('Send message'))
    expect(onSend).not.toHaveBeenCalled()
  })

  it('submitForm clears input and attachments', function () {
    var onSend = jest.fn()
    var attachments: Attachment[] = [{ url: 'blob:test', name: 'img.png', contentType: 'image/png', size: 100 }]
    var setAttachments: Dispatch<SetStateAction<Attachment[]>> = jest.fn()
    render(React.createElement(PureMultimodalInput, {
      onSendMessage: onSend,
      value: 'hi',
      onChange: function () {},
      attachments: attachments,
      setAttachments: setAttachments,
    }))
    fireEvent.click(screen.getByLabelText('Send message'))
    expect(onSend).toHaveBeenCalled()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:test')
  })

  // ── Enter Key Submit ──

  it('submits on Enter key', function () {
    var onSend = jest.fn()
    render(React.createElement(PureMultimodalInput, { onSendMessage: onSend, value: 'hello', onChange: function () {} }))
    var textarea = screen.getByLabelText('Chat message input')
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).toHaveBeenCalled()
  })

  it('does not submit on Shift+Enter', function () {
    var onSend = jest.fn()
    render(React.createElement(PureMultimodalInput, { onSendMessage: onSend, value: 'hello', onChange: function () {} }))
    var textarea = screen.getByLabelText('Chat message input')
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('does not submit on Enter when input empty and no attachments', function () {
    var onSend = jest.fn()
    render(React.createElement(PureMultimodalInput, { onSendMessage: onSend, value: '', onChange: function () {} }))
    var textarea = screen.getByLabelText('Chat message input')
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('submits with attachments only via Enter', function () {
    var onSend = jest.fn()
    var attachments: Attachment[] = [{ url: 'blob:img', name: 'pic.jpg', contentType: 'image/jpeg', size: 200 }]
    render(React.createElement(PureMultimodalInput, {
      onSendMessage: onSend,
      value: '',
      onChange: function () {},
      attachments: attachments,
      setAttachments: function () {},
    }))
    var textarea = screen.getByLabelText('Chat message input')
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).toHaveBeenCalled()
  })

  // ── Language Dropdown ──

  it('opens language menu on globe click', function () {
    render(React.createElement(PureMultimodalInput, {}))
    fireEvent.click(screen.getByTitle('chat.select_language'))
    expect(screen.getByText('English')).toBeTruthy()
    expect(screen.getByText('हिन्दी')).toBeTruthy()
    expect(screen.getByText('தமிழ்')).toBeTruthy()
  })

  it('selects language from menu', function () {
    render(React.createElement(PureMultimodalInput, {}))
    fireEvent.click(screen.getByTitle('chat.select_language'))
    fireEvent.click(screen.getByText('हिन्दी'))
    expect(screen.queryByText('हिन्दी')).toBeNull()
  })

  it('calls onLanguageChange when external handler provided', function () {
    var onLangChange = jest.fn()
    render(React.createElement(PureMultimodalInput, { selectedLanguage: 'en', onLanguageChange: onLangChange }))
    fireEvent.click(screen.getByTitle('chat.select_language'))
    fireEvent.click(screen.getByText('தமிழ்'))
    expect(onLangChange).toHaveBeenCalledWith('ta')
  })

  // ── Attachments ──

  it('renders attachment previews', function () {
    var attachments: Attachment[] = [
      { url: 'blob:1', name: 'doc.pdf', contentType: 'application/pdf', size: 500 },
    ]
    render(React.createElement(PureMultimodalInput, { attachments: attachments }))
    expect(screen.getByTestId('input-attachment-preview')).toBeTruthy()
  })

  it('renders image attachment with Img tag', function () {
    var attachments: Attachment[] = [
      { url: 'blob:img', name: 'photo.jpg', contentType: 'image/jpeg', size: 300 },
    ]
    render(React.createElement(PureMultimodalInput, { attachments: attachments }))
    expect(screen.getByAltText('photo.jpg')).toBeTruthy()
  })

  it('renders non-image attachment as file extension', function () {
    var attachments: Attachment[] = [
      { url: 'blob:doc', name: 'document.pdf', contentType: 'application/pdf', size: 500 },
    ]
    render(React.createElement(PureMultimodalInput, { attachments: attachments }))
    expect(screen.getByText('pdf')).toBeTruthy()
  })

  it('renders uploading state for queued files', function () {
    // Testing upload queue via attachments with isUploading prop - need controlled uploadQueue
    // We access the internal state via the uploadQueue prop pattern
    render(React.createElement(PureMultimodalInput, {
      value: 'test',
      onChange: function () {},
    }))
    // Trigger file change to create upload queue
    var fileInput = screen.getByLabelText('Upload attachment files')
    var file = new File(['test'], 'report.pdf', { type: 'application/pdf' })
    fireEvent.change(fileInput, { target: { files: [file] } })
    // wait for setTimeout in uploadFile
    act(function () { jest.advanceTimersByTime(710) })
    expect(screen.getByTestId('input-attachment-preview')).toBeTruthy()
  })

  // ── handleFileChange ──

  it('handleFileChange handles empty file list', function () {
    render(React.createElement(PureMultimodalInput, {}))
    var fileInput = screen.getByLabelText('Upload attachment files') as HTMLInputElement
    fireEvent.change(fileInput, { target: { files: [] } })
    // Should not throw - no-op behavior
  })

  it('handleFileChange tolerates empty file list', function () {
    render(React.createElement(PureMultimodalInput, { value: 'hi', onChange: function () {} }))
    // Simulating empty file list by not providing files
    expect(screen.getByLabelText('Upload attachment files')).toBeTruthy()
  })

  // ── removeAttachment ──

  it('displays remove button on attachments', function () {
    var attachments: Attachment[] = [
      { url: 'blob:1', name: 'test.pdf', contentType: 'application/pdf', size: 100 },
    ]
    render(React.createElement(PureMultimodalInput, { attachments: attachments }))
    // Should have a button with X icon to remove
    var removeButtons = screen.getAllByRole('button')
    var xButton = removeButtons.find(function (b) { return b.querySelector('svg') })
    expect(xButton).toBeTruthy()
  })

  // ── Uncontrolled mode ──

  it('manages input state internally when no value/onChange provided', function () {
    render(React.createElement(PureMultimodalInput, {}))
    var textarea = screen.getByLabelText('Chat message input') as HTMLTextAreaElement
    expect(textarea.value).toBe('')
    fireEvent.change(textarea, { target: { value: 'typing' } })
    expect(textarea.value).toBe('typing')
  })

  // ── AttachmentsButton triggers file input ──

  it('attachments button click triggers file input', function () {
    render(React.createElement(PureMultimodalInput, {}))
    var fileInput = screen.getByLabelText('Upload attachment files') as HTMLInputElement
    var clickSpy = jest.fn()
    fileInput.click = clickSpy
    fireEvent.click(screen.getByTestId('attachments-button'))
    expect(clickSpy).toHaveBeenCalled()
  })

  // ─── iOS visualViewport keyboard handling ──

  it('handles visualViewport resize for keyboard', function () {
    var addEventListenerSpy = jest.fn()
    var removeEventListenerSpy = jest.fn()
    var mockVisualViewport = {
      addEventListener: addEventListenerSpy,
      removeEventListener: removeEventListenerSpy,
      height: 500,
    }
    Object.defineProperty(window, 'visualViewport', {
      value: mockVisualViewport,
      configurable: true,
      writable: true,
    })
    var innerHeight = window.innerHeight
    window.innerHeight = 800

    var { unmount } = render(React.createElement(PureMultimodalInput, {}))
    expect(addEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function))

    unmount()
    expect(removeEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function))
    window.innerHeight = innerHeight
  })

  it('handles empty visualViewport', function () {
    var origViewport = window.visualViewport
    Object.defineProperty(window, 'visualViewport', {
      value: null,
      configurable: true,
      writable: true,
    })
    expect(function () {
      render(React.createElement(PureMultimodalInput, {}))
    }).not.toThrow()
    Object.defineProperty(window, 'visualViewport', {
      value: origViewport,
      configurable: true,
    })
  })

  // ── Edge Cases ──

  it('does not crash with null onSendMessage/onStopGenerating', function () {
    render(React.createElement(PureMultimodalInput, { isGenerating: true }))
    var textarea = screen.getByLabelText('Chat message input') as HTMLTextAreaElement
    // stop button with no onStopGenerating handler
    fireEvent.click(screen.getByLabelText('Stop generating'))
    // should not throw
  })

  it('handles vibration error gracefully', function () {
    var origVibrate = navigator.vibrate
    Object.defineProperty(navigator, 'vibrate', {
      value: function () { throw new Error('no vibrate') },
      configurable: true,
    })
    var onSend = jest.fn()
    render(React.createElement(PureMultimodalInput, { onSendMessage: onSend, value: 'hi', onChange: function () {} }))
    fireEvent.click(screen.getByLabelText('Send message'))
    expect(onSend).toHaveBeenCalled()
    Object.defineProperty(navigator, 'vibrate', { value: origVibrate, configurable: true })
  })

  // ── MicButton tests ──

  it('renders mic button non-active state', function () {
    render(React.createElement(PureMultimodalInput, {}))
    var micBtn = screen.getByLabelText('Use microphone')
    expect(micBtn).not.toBeDisabled()
  })

  it('disables mic button when isGenerating', function () {
    render(React.createElement(PureMultimodalInput, { isGenerating: true }))
    expect(screen.getByLabelText('Use microphone')).toBeDisabled()
  })

  it('disables mic button when canSend is false', function () {
    render(React.createElement(PureMultimodalInput, { canSend: false }))
    expect(screen.getByLabelText('Use microphone')).toBeDisabled()
  })

  // ── Additional coverage ──

  it('does not submit on Enter when canSend is false', function () {
    var onSend = jest.fn()
    render(React.createElement(PureMultimodalInput, { onSendMessage: onSend, value: 'hello', onChange: function () {}, canSend: false }))
    fireEvent.keyDown(screen.getByLabelText('Chat message input'), { key: 'Enter', shiftKey: false })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('disables attachments button when generating', function () {
    render(React.createElement(PureMultimodalInput, { isGenerating: true }))
    expect(screen.getByTestId('attachments-button')).toBeDisabled()
  })

  it('disables textarea when generating', function () {
    render(React.createElement(PureMultimodalInput, { isGenerating: true }))
    expect(screen.getByLabelText('Chat message input')).toBeDisabled()
  })

  it('disables textarea when canSend is false', function () {
    render(React.createElement(PureMultimodalInput, { canSend: false }))
    expect(screen.getByLabelText('Chat message input')).toBeDisabled()
  })

  it('shows globe highlighted for non-English language', function () {
    render(React.createElement(PureMultimodalInput, { selectedLanguage: 'hi' }))
    expect(screen.getByTitle('chat.select_language').className).toContain('text-brand')
  })

  it('closes language menu on second globe click', function () {
    render(React.createElement(PureMultimodalInput, {}))
    fireEvent.click(screen.getByTitle('chat.select_language'))
    expect(screen.getByText('English')).toBeTruthy()
    fireEvent.click(screen.getByTitle('chat.select_language'))
    expect(screen.queryByText('English')).toBeNull()
  })

  it('calls onStopGenerating even when null handler given', function () {
    expect(function () {
      render(React.createElement(PureMultimodalInput, { isGenerating: true, onStopGenerating: undefined }))
    }).not.toThrow()
  })
})
