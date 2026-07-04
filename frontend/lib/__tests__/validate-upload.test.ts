var mockFileReader = jest.fn()
var mockImage = jest.fn()

var mockCreateElement = document.createElement.bind(document)

describe('validate-upload', function () {
  beforeEach(function () {
    mockFileReader.mockReset()
    mockImage.mockReset()
    document.createElement = mockCreateElement
  })

  afterAll(function () {
    document.createElement = mockCreateElement
  })

  // ── validateImageFile ──

  it('validateImageFile rejects unsupported type', async function () {
    var mod = await import('../validate-upload')
    var file = new File([''], 'test.gif', { type: 'image/gif' })
    var err = mod.validateImageFile(file)
    expect(err).toContain('Unsupported file type')
  })

  it('validateImageFile rejects oversized file', async function () {
    var mod = await import('../validate-upload')
    var file = new File(['x'.repeat(11 * 1024 * 1024)], 'test.jpg', { type: 'image/jpeg' })
    var err = mod.validateImageFile(file)
    expect(err).toContain('exceeds the maximum upload size')
  })

  it('validateImageFile rejects empty file', async function () {
    var mod = await import('../validate-upload')
    var file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    file = Object.defineProperty(file, 'size', { value: 0, writable: true }) as File
    var err = mod.validateImageFile(file)
    expect(err).toContain('empty')
  })

  it('validateImageFile returns null for valid file', async function () {
    var mod = await import('../validate-upload')
    var file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    var err = mod.validateImageFile(file)
    expect(err).toBeNull()
  })

  it('validateImageFile accepts all valid types', async function () {
    var mod = await import('../validate-upload')
    var jpeg = new File(['test'], 'test.jpeg', { type: 'image/jpeg' })
    expect(mod.validateImageFile(jpeg)).toBeNull()
    var webp = new File(['test'], 'test.webp', { type: 'image/webp' })
    expect(mod.validateImageFile(webp)).toBeNull()
    var png = new File(['test'], 'test.png', { type: 'image/png' })
    expect(mod.validateImageFile(png)).toBeNull()
  })

  // ── compressImageFile ──

  it('compressImageFile resolves immediately for small files', async function () {
    var mod = await import('../validate-upload')
    var file = new File(['small'], 'test.jpg', { type: 'image/jpeg' })
    var result = await mod.compressImageFile(file, 1024 * 1024)
    expect(result).toBe(file)
  })

  it('compressImageFile falls back on FileReader error', async function () {
    var origFileReader = globalThis.FileReader
    globalThis.FileReader = jest.fn(function () {
      var reader = {
        onload: null,
        onerror: null,
        readAsDataURL: jest.fn(function () {
          setTimeout(function () { if (reader.onerror) reader.onerror(new Error('read failed')) }, 0)
        }),
      }
      return reader
    }) as any
    var mod = await import('../validate-upload')
    var file = new File(['x'.repeat(2 * 1024 * 1024)], 'test.jpg', { type: 'image/jpeg' })
    var result = await mod.compressImageFile(file, 100)
    expect(result).toBe(file)
    globalThis.FileReader = origFileReader
  })

  it('compressImageFile falls back on getContext returning null', async function () {
    var origCreateElement = document.createElement
    document.createElement = function (tag: string) {
      if (tag === 'canvas') {
        return { width: 0, height: 0, getContext: function () { return null }, toBlob: jest.fn() } as any
      }
      return origCreateElement.call(document, tag)
    }
    var origFileReader = globalThis.FileReader
    globalThis.FileReader = jest.fn(function () {
      var reader = {
        onload: null,
        onerror: null,
        readAsDataURL: jest.fn(function () {
          setTimeout(function () {
            if (reader.onload) reader.onload({ target: { result: 'data:image/png;base64,iVBOR' } })
          }, 0)
        }),
      }
      return reader
    }) as any
    var origImage = globalThis.Image
    globalThis.Image = jest.fn(function () {
      var img = { width: 2000, height: 1500, onload: null, onerror: null, src: '' }
      setTimeout(function () { if (img.onload) img.onload(new Event('load')) }, 0)
      return img
    }) as any
    var mod = await import('../validate-upload')
    var file = new File(['x'.repeat(2 * 1024 * 1024)], 'test.jpg', { type: 'image/jpeg' })
    var result = await mod.compressImageFile(file, 100)
    expect(result).toBe(file)
    globalThis.FileReader = origFileReader
    globalThis.Image = origImage
    document.createElement = origCreateElement
  })

  it('compressImageFile falls back on Image onerror', async function () {
    var origFileReader = globalThis.FileReader
    globalThis.FileReader = jest.fn(function () {
      var reader = {
        onload: null,
        onerror: null,
        readAsDataURL: jest.fn(function () {
          setTimeout(function () {
            if (reader.onload) reader.onload({ target: { result: 'data:image/png;base64,iVBOR' } })
          }, 0)
        }),
      }
      return reader
    }) as any
    var origImage = globalThis.Image
    globalThis.Image = jest.fn(function () {
      var img = { onload: null, onerror: null, src: '' }
      setTimeout(function () { if (img.onerror) img.onerror(new Event('error')) }, 0)
      return img
    }) as any
    var mod = await import('../validate-upload')
    var file = new File(['x'.repeat(2 * 1024 * 1024)], 'test.jpg', { type: 'image/jpeg' })
    var result = await mod.compressImageFile(file, 100)
    expect(result).toBe(file)
    globalThis.FileReader = origFileReader
    globalThis.Image = origImage
  })

  it('compressImageFile falls back on toBlob returning null', async function () {
    var createCanvas = function () { return { width: 0, height: 0, getContext: function () { return { drawImage: jest.fn() } }, toBlob: function (cb: Function) { setTimeout(function () { cb(null) }, 0) } } }
    var origCreateElement = document.createElement
    document.createElement = function (tag: string) {
      if (tag === 'canvas') return createCanvas()
      return origCreateElement.call(document, tag)
    }
    var origFileReader = globalThis.FileReader
    globalThis.FileReader = jest.fn(function () {
      var reader = {
        onload: null,
        onerror: null,
        readAsDataURL: jest.fn(function () {
          setTimeout(function () {
            if (reader.onload) reader.onload({ target: { result: 'data:image/png;base64,iVBOR' } })
          }, 0)
        }),
      }
      return reader
    }) as any
    var origImage = globalThis.Image
    globalThis.Image = jest.fn(function () {
      var img = { width: 100, height: 100, onload: null, onerror: null, src: '' }
      setTimeout(function () { if (img.onload) img.onload(new Event('load')) }, 0)
      return img
    }) as any
    var mod = await import('../validate-upload')
    var file = new File(['x'.repeat(2 * 1024 * 1024)], 'test.jpg', { type: 'image/jpeg' })
    var result = await mod.compressImageFile(file, 100)
    expect(result).toBe(file)
    globalThis.FileReader = origFileReader
    globalThis.Image = origImage
    document.createElement = origCreateElement
  })

  it('compressImageFile succeeds with valid canvas', async function () {
    var createCanvas = function () {
      var ctx = { drawImage: jest.fn() }
      return { width: 0, height: 0, getContext: function () { return ctx }, toBlob: function (cb: Function) { setTimeout(function () { cb(new Blob(['compressed'])) }, 0) } }
    }
    var origCreateElement = document.createElement
    document.createElement = function (tag: string) {
      if (tag === 'canvas') return createCanvas()
      return origCreateElement.call(document, tag)
    }
    var origFileReader = globalThis.FileReader
    globalThis.FileReader = jest.fn(function () {
      var reader = {
        onload: null,
        onerror: null,
        readAsDataURL: jest.fn(function () {
          setTimeout(function () {
            if (reader.onload) reader.onload({ target: { result: 'data:image/jpeg;base64,/9j/' } })
          }, 0)
        }),
      }
      return reader
    }) as any
    var origImage = globalThis.Image
    globalThis.Image = jest.fn(function () {
      var img = { width: 3840, height: 2160, onload: null, onerror: null, src: '' }
      setTimeout(function () { if (img.onload) img.onload(new Event('load')) }, 0)
      return img
    }) as any
    var mod = await import('../validate-upload')
    var file = new File(['x'.repeat(2 * 1024 * 1024)], 'test.jpg', { type: 'image/jpeg' })
    var result = await mod.compressImageFile(file, 100)
    expect(result).not.toBe(file)
    expect(result.name).toContain('.jpg')
    globalThis.FileReader = origFileReader
    globalThis.Image = origImage
    document.createElement = origCreateElement
  })

  it('compressImageFile handles tall image (height > width)', async function () {
    var createCanvas = function () {
      var ctx = { drawImage: jest.fn() }
      return { width: 0, height: 0, getContext: function () { return ctx }, toBlob: function (cb: Function) { setTimeout(function () { cb(new Blob(['tall'])) }, 0) } }
    }
    var origCreateElement = document.createElement
    document.createElement = function (tag: string) {
      if (tag === 'canvas') return createCanvas()
      return origCreateElement.call(document, tag)
    }
    var origFileReader = globalThis.FileReader
    globalThis.FileReader = jest.fn(function () {
      var reader = { onload: null, onerror: null, readAsDataURL: jest.fn(function () { setTimeout(function () { if (reader.onload) reader.onload({ target: { result: 'data:image/jpeg;base64,/9j/' } }) }, 0) }) }
      return reader
    }) as any
    var origImage = globalThis.Image
    globalThis.Image = jest.fn(function () {
      var img = { width: 1080, height: 1920, onload: null, onerror: null, src: '' }
      setTimeout(function () { if (img.onload) img.onload(new Event('load')) }, 0)
      return img
    }) as any
    var mod = await import('../validate-upload')
    var file = new File(['x'.repeat(2 * 1024 * 1024)], 'test.jpg', { type: 'image/jpeg' })
    var result = await mod.compressImageFile(file, 100)
    expect(result).not.toBe(file)
    globalThis.FileReader = origFileReader
    globalThis.Image = origImage
    document.createElement = origCreateElement
  })

  // ── Export constants ──

  it('exports constants', async function () {
    var mod = await import('../validate-upload')
    expect(mod.ALLOWED_IMAGE_TYPES).toEqual(['image/jpeg', 'image/png', 'image/webp'])
    expect(mod.MAX_UPLOAD_BYTES).toBe(10 * 1024 * 1024)
    expect(mod.VALID_MAGIC_BYTES['image/jpeg']).toBeDefined()
  })
})
