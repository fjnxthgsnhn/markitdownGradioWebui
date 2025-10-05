import sys
from typing import Any, Union, BinaryIO
from .._stream_info import StreamInfo
from .._base_converter import DocumentConverter, DocumentConverterResult
from .._exceptions import MissingDependencyException, MISSING_DEPENDENCY_MESSAGE
import email
from email import policy
from email.parser import BytesParser

# Try loading optional dependencies
_dependency_exc_info = None

ACCEPTED_MIME_TYPE_PREFIXES = [
    "message/rfc822",
    "application/vnd.ms-outlook",
]

ACCEPTED_FILE_EXTENSIONS = [".eml", ".msg"]


class EmailConverter(DocumentConverter):
    """Converts email files (.eml, .msg) to markdown by extracting email metadata and content.

    Uses the email package to parse email files and extract:
    - Email headers (From, To, Subject, Date)
    - Email body content
    - Attachments (if any)
    """

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> bool:
        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()

        # Check the extension and mimetype
        if extension in ACCEPTED_FILE_EXTENSIONS:
            return True

        for prefix in ACCEPTED_MIME_TYPE_PREFIXES:
            if mimetype.startswith(prefix):
                return True

        return False

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> DocumentConverterResult:
        # Check: the dependencies
        if _dependency_exc_info is not None:
            raise MissingDependencyException(
                MISSING_DEPENDENCY_MESSAGE.format(
                    converter=type(self).__name__,
                    extension=".eml/.msg",
                    feature="email",
                )
            ) from _dependency_exc_info[
                1
            ].with_traceback(  # type: ignore[union-attr]
                _dependency_exc_info[2]
            )

        # Parse the email
        file_stream.seek(0)
        msg = BytesParser(policy=policy.default).parse(file_stream)
        
        # Extract email metadata
        md_content = "# Email Message\n\n"

        # Get headers
        headers = {
            "From": self._decode_header(msg.get("From", "")),
            "To": self._decode_header(msg.get("To", "")),
            "Subject": self._decode_header(msg.get("Subject", "")),
            "Date": msg.get("Date", ""),
            "CC": self._decode_header(msg.get("CC", "")),
        }

        # Add headers to markdown
        for key, value in headers.items():
            if value:
                md_content += f"**{key}:** {value}\n"

        md_content += "\n## Content\n\n"

        # Extract email body
        body = self._extract_body(msg)
        if body:
            md_content += body

        return DocumentConverterResult(
            markdown=md_content.strip(),
            title=headers.get("Subject"),
        )

    def _decode_header(self, header_value: str) -> str:
        """Decode email header with proper character encoding."""
        if not header_value:
            return ""
        
        try:
            # Use email.header.decode_header to handle encoded headers
            from email.header import decode_header
            decoded_parts = []
            for part, encoding in decode_header(header_value):
                if isinstance(part, bytes):
                    if encoding:
                        try:
                            decoded_parts.append(part.decode(encoding))
                        except (UnicodeDecodeError, LookupError):
                            # Fallback to common encodings
                            for enc in ['utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']:
                                try:
                                    decoded_parts.append(part.decode(enc))
                                    break
                                except UnicodeDecodeError:
                                    continue
                            else:
                                decoded_parts.append(part.decode('utf-8', errors='ignore'))
                    else:
                        # Try common encodings
                        for enc in ['utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']:
                            try:
                                decoded_parts.append(part.decode(enc))
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            decoded_parts.append(part.decode('utf-8', errors='ignore'))
                else:
                    decoded_parts.append(part)
            
            return "".join(decoded_parts)
        except Exception:
            return header_value

    def _extract_body(self, msg) -> str:
        """Extract the main body content from the email."""
        body = ""
        
        if msg.is_multipart():
            # Handle multipart messages
            for part in msg.iter_parts():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Prefer text/plain over text/html
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body = payload.decode(charset)
                            break
                        except (UnicodeDecodeError, LookupError):
                            # Try common encodings
                            for enc in ['utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']:
                                try:
                                    body = payload.decode(enc)
                                    break
                                except UnicodeDecodeError:
                                    continue
                            else:
                                body = payload.decode('utf-8', errors='ignore')
                elif content_type == "text/html" and not body:
                    # Use HTML as fallback if no plain text found
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body = payload.decode(charset)
                        except (UnicodeDecodeError, LookupError):
                            for enc in ['utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']:
                                try:
                                    body = payload.decode(enc)
                                    break
                                except UnicodeDecodeError:
                                    continue
                            else:
                                body = payload.decode('utf-8', errors='ignore')
        else:
            # Single part message
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                try:
                    body = payload.decode(charset)
                except (UnicodeDecodeError, LookupError):
                    for enc in ['utf-8', 'shift_jis', 'cp932', 'iso-2022-jp']:
                        try:
                            body = payload.decode(enc)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        body = payload.decode('utf-8', errors='ignore')
        
        return body
