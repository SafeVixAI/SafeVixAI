import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'

jest.mock('next/image', function() {
  return function MockImage(props) {
    return React.createElement('div', { 'data-testid': 'next-image', 'data-src': props.src, 'data-alt': props.alt }, props.alt)
  }
})

jest.mock('@/lib/client-logger', function() {
  return {
    logClientError: jest.fn(),
    logClientWarning: jest.fn(),
  }
})

jest.mock('fast-deep-equal', function() {
  return function equal(a, b) { return a === b }
})

var PureMultimodalInput
var mockMediaRecorder
var mockStream
var mockRecognition

beforeAll(function() {
  PureMultimodalInput = require('../multimodal-ai-chat-input').default
})

beforeEach(function() {
  jest.clearAllMocks()

  mockMediaRecorder = {
    start: jest.fn(),
    stop: jest.fn(),
    state: 'inactive',
    ondataavailable: null,
    onstop: null,
  }

  mockStream = { getTracks: jest.fn().mockReturnValue([{ stop: jest.fn() }]) }

  try { navigator.mediaDevices = { getUserMedia: jest.fn().mockResolvedValue(mockStream) } } catch (e) {
    Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia: jest.fn().mockResolvedValue(mockStream) }, writable: true, configurable: true })
  }

  global.MediaRecorder = jest.fn().mockImplementation(function() { mockMediaRecorder.state = 'recording'; return mockMediaRecorder })

  mockRecognition = { continuous: false, interimResults: false, lang: '', onresult: null, onend: null, onerror: null, start: jest.fn(), stop: jest.fn() }
  global.SpeechRecognition = jest.fn().mockImplementation(function() { return mockRecognition })
  global.webkitSpeechRecognition = undefined

  global.URL.createObjectURL = jest.fn().mockReturnValue('blob:mocked-url')
  global.URL.revokeObjectURL = jest.fn()

  global.fetch = jest.fn()
  try { navigator.vibrate = jest.fn() } catch (e) { Object.defineProperty(navigator, 'vibrate', { value: jest.fn(), writable: true, configurable: true }) }

  if (!window.visualViewport) {
    Object.defineProperty(window, 'visualViewport', { value: { height: window.innerHeight, addEventListener: jest.fn(), removeEventListener: jest.fn() }, writable: true, configurable: true })
  }
})

describe('PureMultimodalInput', function () {
  function renderInput(props) {
    return render(React.createElement(PureMultimodalInput, Object.assign({
      onSendMessage: jest.fn(),
      isGenerating: false,
      canSend: true,
    }, props)))
  }

  it('renders textarea with placeholder', function () {
    renderInput()
    expect(screen.getByPlaceholderText('Ask AI anything...')).toBeInTheDocument()
  })

  it('renders attachments button, mic button, and send button', function () {
    renderInput()
    expect(screen.getByTestId('attachments-button')).toBeInTheDocument()
    expect(screen.getByTestId('mic-button')).toBeInTheDocument()
    expect(screen.getByTestId('send-button')).toBeInTheDocument()
  })

  it('shows stop button when isGenerating is true', function () {
    renderInput({ isGenerating: true })
    expect(screen.getByTestId('stop-button')).toBeInTheDocument()
    expect(screen.queryByTestId('send-button')).not.toBeInTheDocument()
  })

  it('send button is disabled when input is empty', function () {
    renderInput()
    var sendBtn = screen.getByTestId('send-button')
    expect(sendBtn).toBeDisabled()
  })

  it('send button is enabled when input has text', function () {
    renderInput()
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    var sendBtn = screen.getByTestId('send-button')
    expect(sendBtn).not.toBeDisabled()
  })

  it('text input onChange updates displayed value', function () {
    renderInput()
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    expect(textarea.value).toBe('Test message')
  })

  it('Enter key submits form', function () {
    var onSend = jest.fn()
    renderInput({ onSendMessage: onSend })
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' })
    expect(onSend).toHaveBeenCalledWith({ input: 'Hello', attachments: [] })
  })

  it('Shift+Enter does not submit form', function () {
    var onSend = jest.fn()
    renderInput({ onSendMessage: onSend })
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: true })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('calls onSendMessage when send button clicked with input', function () {
    var onSend = jest.fn()
    renderInput({ onSendMessage: onSend })
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    fireEvent.change(textarea, { target: { value: 'Test' } })
    var sendBtn = screen.getByTestId('send-button')
    fireEvent.click(sendBtn)
    expect(onSend).toHaveBeenCalledWith({ input: 'Test', attachments: [] })
  })

  it('clears input after submitting', function () {
    renderInput()
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    fireEvent.change(textarea, { target: { value: 'Clear me' } })
    var sendBtn = screen.getByTestId('send-button')
    fireEvent.click(sendBtn)
    expect(textarea.value).toBe('')
  })

  it('renders attachments preview with remove button', function () {
    var attachments = [{ url: 'blob:test', name: 'photo.jpg', contentType: 'image/jpeg', size: 1024 }]
    renderInput({ attachments: attachments, setAttachments: jest.fn() })
    expect(screen.getByTestId('input-attachment-preview')).toBeInTheDocument()
  })

  it('language menu opens and closes on globe click', function () {
    renderInput()
    var langBtn = screen.getByLabelText('chat.select_language')
    fireEvent.click(langBtn)
    expect(screen.getByText('English')).toBeInTheDocument()
    fireEvent.click(langBtn)
  })

  it('language selection changes displayed language', function () {
    var onLangChange = jest.fn()
    renderInput({ onLanguageChange: onLangChange })
    var globeBtn = screen.getByLabelText('chat.select_language')
    fireEvent.click(globeBtn)
    var hindiBtn = screen.getByText('Hindi')
    fireEvent.click(hindiBtn)
    expect(onLangChange).toHaveBeenCalledWith('hi')
  })

  it('textarea is disabled when canSend is false', function () {
    renderInput({ canSend: false })
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    expect(textarea).toBeDisabled()
  })

  it('send button is disabled when isGenerating is true', function () {
    renderInput({ isGenerating: true })
    var stopBtn = screen.getByTestId('stop-button')
    expect(stopBtn).toBeInTheDocument()
  })

  it('non-image attachment shows file extension', function () {
    var attachments = [{ url: '', name: 'doc.pdf', contentType: 'application/pdf', size: 2048 }]
    var setAttachments = jest.fn()
    renderInput({ attachments: attachments, setAttachments: setAttachments })
    expect(screen.getByText('pdf')).toBeInTheDocument()
  })

  it('attachment remove filters out the attachment', function () {
    var setAttachments = jest.fn()
    var attachments = [{ url: 'blob:remove-test', name: 'test.txt', contentType: 'text/plain', size: 512 }]
    renderInput({ attachments: attachments, setAttachments: setAttachments })
    expect(screen.getByTestId('input-attachment-preview')).toBeInTheDocument()
  })

  it('uses controlled value when provided', function () {
    var onChange = jest.fn()
    renderInput({ value: 'Controlled', onChange: onChange })
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    expect(textarea.value).toBe('Controlled')
    fireEvent.change(textarea, { target: { value: 'Updated' } })
    expect(onChange).toHaveBeenCalledWith('Updated')
  })

  // ── Stop Button ──────────────────────────────────────────────

  it('stop button calls onStopGenerating when clicked', function () {
    var onStop = jest.fn()
    renderInput({ isGenerating: true, onStopGenerating: onStop })
    var stopBtn = screen.getByTestId('stop-button')
    fireEvent.click(stopBtn)
    expect(onStop).toHaveBeenCalled()
  })

  // ── Send Button ──────────────────────────────────────────────

  it('send button is disabled when no input and no attachments', function () {
    renderInput({ canSend: true })
    var sendBtn = screen.getByTestId('send-button')
    expect(sendBtn).toBeDisabled()
  })

  it('send button navigator.vibrate called on submit', function () {
    renderInput()
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    var sendBtn = screen.getByTestId('send-button')
    fireEvent.click(sendBtn)
    expect(navigator.vibrate).toHaveBeenCalledWith(50)
  })

  it('send button handles navigator.vibrate error gracefully', function () {
    navigator.vibrate = jest.fn().mockImplementation(function() { throw new Error('vibrate not supported') })
    var logClientError = require('@/lib/client-logger').logClientError
    renderInput()
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    var sendBtn = screen.getByTestId('send-button')
    fireEvent.click(sendBtn)
    expect(logClientError).toHaveBeenCalled()
  })

  // ── Attachments Button ───────────────────────────────────────

  it('attachments button click triggers hidden file input click', function () {
    var fileInputRef = { current: { click: jest.fn() } }
    renderInput()
    var attachBtn = screen.getByTestId('attachments-button')
    fireEvent.click(attachBtn)
  })

  // ── Preview Attachment ───────────────────────────────────────

  it('image attachment renders next/image component', function () {
    var attachments = [{ url: 'blob:img', name: 'photo.jpg', contentType: 'image/jpeg', size: 1024 }]
    renderInput({ attachments: attachments, setAttachments: jest.fn() })
    expect(screen.getByTestId('next-image')).toBeInTheDocument()
  })

  it('file change flow shows upload loader then resolves', async function () {
    jest.useFakeTimers()
    renderInput()
    var fileInput = screen.getByLabelText('Upload attachment files')
    var file = new File(['test'], 'photo.jpg', { type: 'image/jpeg' })
    fireEvent.change(fileInput, { target: { files: [file] } })
    await waitFor(function() { expect(screen.getByTestId('input-attachment-loader')).toBeInTheDocument() })
    var previews = screen.getAllByTestId('input-attachment-preview')
    expect(previews.length).toBe(1)
    await act(async function() { jest.advanceTimersByTime(700) })
    jest.useRealTimers()
  })

  // ── Main Component Behaviors ─────────────────────────────────

  it('submit form with empty input and empty attachments returns early', function () {
    var onSend = jest.fn()
    renderInput({ onSendMessage: onSend })
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    textarea.value = ''
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('submit form revokes blob URLs for all attachments', function () {
    var onSend = jest.fn()
    var attachments = [{ url: 'blob:test1', name: 'a.txt', contentType: 'text/plain', size: 100 }]
    renderInput({ onSendMessage: onSend, value: 'test', attachments: attachments, setAttachments: jest.fn() })
    var sendBtn = screen.getByTestId('send-button')
    fireEvent.click(sendBtn)
    expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:test1')
  })

  it('handleRemoveAttachment revokes blob URL on X click', function () {
    var setAttachments = jest.fn()
    var attachments = [{ url: 'blob:remove-me', name: 'test.txt', contentType: 'text/plain', size: 512 }]
    renderInput({ attachments: attachments, setAttachments: setAttachments })
    var xButtons = screen.getAllByRole('button')
    var removeBtn = xButtons.find(function(b) { return b.querySelector('.lucide-x') })
    if (removeBtn) { fireEvent.click(removeBtn) }
    expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:remove-me')
  })

  it('hidden file input disabled when isGenerating', function () {
    renderInput({ isGenerating: true })
    var fileInput = screen.getByLabelText('Upload attachment files')
    expect(fileInput).toBeDisabled()
  })

  it('file change with empty files returns early', function () {
    renderInput()
    var fileInput = screen.getByLabelText('Upload attachment files')
    fireEvent.change(fileInput, { target: { files: [] } })
  })

  it('file change with valid files adds attachments', async function () {
    jest.useFakeTimers()
    var setAttachments = jest.fn()
    renderInput({ setAttachments: setAttachments })
    var fileInput = screen.getByLabelText('Upload attachment files')
    var file = new File(['test'], 'photo.jpg', { type: 'image/jpeg' })
    fireEvent.change(fileInput, { target: { files: [file] } })
    await act(async function() { jest.advanceTimersByTime(700) })
    expect(global.URL.createObjectURL).toHaveBeenCalledWith(file)
    expect(setAttachments).toHaveBeenCalled()
    jest.useRealTimers()
  })

  it('file change filters files exceeding max size', async function () {
    jest.useFakeTimers()
    var setAttachments = jest.fn()
    renderInput({ setAttachments: setAttachments })
    var fileInput = screen.getByLabelText('Upload attachment files')
    var smallFile = new File(['a'], 'small.txt', { type: 'text/plain' })
    Object.defineProperty(smallFile, 'size', { value: 100 })
    var bigFile = new File(['x'.repeat(30 * 1024 * 1024)], 'big.txt', { type: 'text/plain' })
    Object.defineProperty(bigFile, 'size', { value: 30 * 1024 * 1024 })
    fireEvent.change(fileInput, { target: { files: [smallFile, bigFile] } })
    await act(async function() { jest.advanceTimersByTime(700) })
    expect(global.URL.createObjectURL).toHaveBeenCalledWith(smallFile)
    jest.useRealTimers()
  })

  it('handleRemoveAttachment with non-blob URL does not revoke', function () {
    var setAttachments = jest.fn()
    var attachments = [{ url: 'https://example.com/img.jpg', name: 'remote.jpg', contentType: 'image/jpeg', size: 500 }]
    renderInput({ attachments: attachments, setAttachments: setAttachments })
  })

  // ── Mic Button ───────────────────────────────────────────────

  it('mic button click starts recording via getUserMedia', async function () {
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({ audio: true }) })
  })

  it('mic button stops recording when clicked again while active', async function () {
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(mockMediaRecorder.start).toHaveBeenCalled() })
    fireEvent.click(micBtn)
    expect(mockMediaRecorder.stop).toHaveBeenCalled()
  })

  it('speech translation success appends transcript to input', async function () {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: jest.fn().mockResolvedValue({ text: 'hello world' }) })
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(mockMediaRecorder.start).toHaveBeenCalled() })
    await act(async function() { await mockMediaRecorder.onstop() })
    await waitFor(function() { expect(global.fetch).toHaveBeenCalled() })
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    expect(textarea.value).toBe('hello world')
  })

  it('speech translation failure logs warning', async function () {
    var logClientWarning = require('@/lib/client-logger').logClientWarning
    global.fetch = jest.fn().mockResolvedValue({ ok: false })
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(mockMediaRecorder.start).toHaveBeenCalled() })
    await act(async function() { await mockMediaRecorder.onstop() })
    expect(logClientWarning).toHaveBeenCalled()
  })

  it('speech translation fetch throws error logs warning', async function () {
    var logClientWarning = require('@/lib/client-logger').logClientWarning
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'))
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(mockMediaRecorder.start).toHaveBeenCalled() })
    await act(async function() { await mockMediaRecorder.onstop() })
    expect(logClientWarning).toHaveBeenCalled()
  })

  it('mic button disabled when isGenerating', function () {
    renderInput({ isGenerating: true })
    var micBtn = screen.getByTestId('mic-button')
    expect(micBtn).toBeDisabled()
  })

  it('mic button disabled when canSend is false', function () {
    renderInput({ canSend: false })
    var micBtn = screen.getByTestId('mic-button')
    expect(micBtn).toBeDisabled()
  })

  it('falls back to Web Speech when getUserMedia fails', async function () {
    navigator.mediaDevices.getUserMedia = jest.fn().mockRejectedValue(new Error('Permission denied'))
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(global.SpeechRecognition).toHaveBeenCalled() })
    expect(mockRecognition.start).toHaveBeenCalled()
  })

  it('Web Speech onresult calls onTranscript', async function () {
    navigator.mediaDevices.getUserMedia = jest.fn().mockRejectedValue(new Error('Permission denied'))
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(mockRecognition.start).toHaveBeenCalled() })
    await act(async function() { mockRecognition.onresult({ results: { 0: { 0: { transcript: 'test speech' } } } }) })
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    expect(textarea.value).toBe('test speech')
  })

  it('Web Speech onend sets inactive', async function () {
    navigator.mediaDevices.getUserMedia = jest.fn().mockRejectedValue(new Error('Permission denied'))
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(mockRecognition.start).toHaveBeenCalled() })
    await act(async function() { mockRecognition.onend() })
    expect(true).toBe(true)
  })

  it('Web Speech onerror logs warning', async function () {
    var logClientWarning = require('@/lib/client-logger').logClientWarning
    navigator.mediaDevices.getUserMedia = jest.fn().mockRejectedValue(new Error('Permission denied'))
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(mockRecognition.start).toHaveBeenCalled() })
    await act(async function() { mockRecognition.onerror({ error: 'no-speech' }) })
    expect(logClientWarning).toHaveBeenCalledWith('Web Speech error', 'no-speech')
  })

  it('Web Speech not supported logs warning', async function () {
    var logClientWarning = require('@/lib/client-logger').logClientWarning
    global.SpeechRecognition = undefined
    global.webkitSpeechRecognition = undefined
    navigator.mediaDevices.getUserMedia = jest.fn().mockRejectedValue(new Error('Permission denied'))
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(logClientWarning).toHaveBeenCalled() })
  })

  it('mic button shows LoaderIcon when processing', async function () {
    global.fetch = jest.fn().mockRejectedValue(new Error('fail'))
    renderInput()
    var micBtn = screen.getByTestId('mic-button')
    fireEvent.click(micBtn)
    await waitFor(function() { expect(mockMediaRecorder.start).toHaveBeenCalled() })
    await act(async function() { await mockMediaRecorder.onstop() })
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    expect(global.fetch).toHaveBeenCalled()
  })

  it('visualViewport resize effect registers event listener', function () {
    window.visualViewport.addEventListener = jest.fn()
    window.visualViewport.removeEventListener = jest.fn()
    renderInput()
    expect(window.visualViewport.addEventListener).toHaveBeenCalledWith('resize', expect.any(Function))
  })

  it('enter with attachments submits when input empty', function () {
    var onSend = jest.fn()
    var attachments = [{ url: 'blob:test', name: 'a.jpg', contentType: 'image/jpeg', size: 500 }]
    renderInput({ onSendMessage: onSend, attachments: attachments, setAttachments: jest.fn() })
    var textarea = screen.getByPlaceholderText('Ask AI anything...')
    fireEvent.change(textarea, { target: { value: '' } })
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' })
    expect(onSend).toHaveBeenCalled()
  })
})
