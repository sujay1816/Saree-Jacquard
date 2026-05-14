/**
 * Tiny zip reader for our specific use case: reading the BMPs and preview.png
 * out of the backend's response zip in the browser so we can show thumbnails.
 *
 * Supports STORE (no compression) and DEFLATE. Uses the browser's built-in
 * DecompressionStream API (available in all modern browsers).
 *
 * Not a general-purpose zip library; deliberately minimal to avoid adding
 * JSZip (~100KB) just for reading our own output.
 */

const EOCD_SIGNATURE = 0x06054b50;
const CENTRAL_DIR_SIGNATURE = 0x02014b50;
const LOCAL_FILE_SIGNATURE = 0x04034b50;

async function blobToArrayBuffer(blob) {
  // Modern browsers all support Blob.prototype.arrayBuffer
  return await blob.arrayBuffer();
}

async function inflateRaw(deflated) {
  // Browser's built-in DecompressionStream handles raw DEFLATE (no zlib wrapper)
  // when the format is 'deflate-raw'.
  const stream = new Blob([deflated]).stream().pipeThrough(
    new DecompressionStream('deflate-raw')
  );
  const reader = stream.getReader();
  const chunks = [];
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }
  // Concat
  const total = chunks.reduce((n, c) => n + c.byteLength, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const c of chunks) {
    out.set(c, offset);
    offset += c.byteLength;
  }
  return out;
}

async function read(blob) {
  const buf = await blobToArrayBuffer(blob);
  const view = new DataView(buf);
  const bytes = new Uint8Array(buf);
  const decoder = new TextDecoder('utf-8');

  // Find end-of-central-directory record (scan from end for signature)
  let eocdOffset = -1;
  for (let i = bytes.length - 22; i >= Math.max(0, bytes.length - 65557); i--) {
    if (view.getUint32(i, true) === EOCD_SIGNATURE) {
      eocdOffset = i;
      break;
    }
  }
  if (eocdOffset < 0) throw new Error('Not a zip file: EOCD not found');

  const numEntries = view.getUint16(eocdOffset + 10, true);
  const cdOffset = view.getUint32(eocdOffset + 16, true);

  const entries = [];
  let pos = cdOffset;

  for (let i = 0; i < numEntries; i++) {
    if (view.getUint32(pos, true) !== CENTRAL_DIR_SIGNATURE) {
      throw new Error('Corrupt central directory at entry ' + i);
    }
    const compressionMethod = view.getUint16(pos + 10, true);
    const compressedSize = view.getUint32(pos + 20, true);
    const uncompressedSize = view.getUint32(pos + 24, true);
    const fileNameLength = view.getUint16(pos + 28, true);
    const extraFieldLength = view.getUint16(pos + 30, true);
    const fileCommentLength = view.getUint16(pos + 32, true);
    const localHeaderOffset = view.getUint32(pos + 42, true);

    const fileName = decoder.decode(
      bytes.subarray(pos + 46, pos + 46 + fileNameLength)
    );

    // Read local file header to find where the data actually starts
    if (view.getUint32(localHeaderOffset, true) !== LOCAL_FILE_SIGNATURE) {
      throw new Error('Corrupt local file header for ' + fileName);
    }
    const localFileNameLength = view.getUint16(localHeaderOffset + 26, true);
    const localExtraFieldLength = view.getUint16(localHeaderOffset + 28, true);
    const dataStart =
      localHeaderOffset + 30 + localFileNameLength + localExtraFieldLength;
    const compressedData = bytes.subarray(dataStart, dataStart + compressedSize);

    let data;
    if (compressionMethod === 0) {
      // Stored - no compression
      data = compressedData;
    } else if (compressionMethod === 8) {
      // DEFLATE
      data = await inflateRaw(compressedData);
    } else {
      throw new Error(
        `Unsupported zip compression method ${compressionMethod} for ${fileName}`
      );
    }

    entries.push({ name: fileName, data, uncompressedSize });
    pos +=
      46 + fileNameLength + extraFieldLength + fileCommentLength;
  }

  return entries;
}

export default { read };
