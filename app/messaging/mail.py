from settings import Settings, Messaging
from utils import Logger
import typing
import smtplib
import ssl
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _divide_to_subject_body(body: str) -> typing.Tuple[str, str]:
    """
    Splits given text to subject and body if found
    Subject is from body divided with one empty line
    If there is no empty line or there is small number of lines, returns empty subject and untouched body
    Returns tuple of (subject: str, body: str)
    >>> text = "Subject from me\\n \\nBody from me, to be sent\\nHere you go"
    >>> subject, body = _divide_to_subject_body(text)
    >>> # subject = "Subject from me"
    >>> # body = "Body from me, to be sent\\nHere you go"
    """
    Logger.log(4, "mail.divide_subject_to_body()")
    body_divided = body.split("\n")

    if len(body_divided) < 3:
        return "", body

    if body_divided[1].strip() != "":
        return "", body

    body_divided.pop(1)

    return body_divided[0], "\n".join(body_divided[1:])


def connect(host: str, port: int, login: str = "", password: str = "", encryption_method: str = "TLS")\
        -> typing.Union[None, smtplib.SMTP, smtplib.SMTP_SSL]:
    """
    Opens connection to specified server with parameters. If some error occurred, returns None
    Possible values for encryption_method: SSL, TLS, STARTTLS, ANY
    Possible errors:
     - host (with port) is not correct
     - server does not support encryption method provided (on selected port)
     - timeout
     - login or password is not correct
    """
    Logger.log(4, f"mail.connect(host={host},port={port},login={login},encryption={encryption_method})")
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    try:

        if encryption_method in ("SSL", "TLS"):
            # explicit mode requested, server must support SSL or TLS
            # https://docs.python.org/3/library/smtplib.html#smtplib.SMTP_SSL
            smtp_connection = smtplib.SMTP_SSL(host=host, port=port, timeout=5, context=context)
        else:
            # implicit mode requested, communication starts unencrypted,
            # later, if server supports (starttls) can be upgraded
            # https://docs.python.org/3/library/smtplib.html#smtplib.SMTP
            smtp_connection = smtplib.SMTP(host=host, port=port, timeout=5)

    except smtplib.SMTPConnectError as e:
        Logger.log(2, f"Could not connect to SMTP server {host}:{port}. Hostname or port is wrong. Error text: {e}")
        return None
    except TimeoutError as e:
        Logger.log(2, f"Could not connect to SMTP server {host}{port}. Time is up. Error text: {e}")
        return None

    if encryption_method == "STARTTLS":
        # implicit method, negotiating encryption
        smtp_connection.starttls(context=context)

    # https://docs.python.org/3/library/smtplib.html#smtplib.SMTP.ehlo_or_helo_if_needed
    try:
        smtp_connection.ehlo_or_helo_if_needed()
    except smtplib.SMTPHeloError as e:
        Logger.log(2, f"We could not understand HELO/EHLO from {host}:{port}. Error text: {e}")
        smtp_connection.quit()
        return None

    # https://docs.python.org/3/library/smtplib.html#smtplib.SMTP.login
    if login and password:
        # SMTP must authenticate and authorize me
        try:
            smtp_connection.login(login, password)
        except smtplib.SMTPAuthenticationError as e:
            Logger.log(2, f"Username and password are not accepted by {host}:{port}. Error text: {e}")
            smtp_connection.quit()
            return None
        except smtplib.SMTPNotSupportedError as e:
            Logger.log(2, f"Server {host}:{port} does not accept authentication. Error text: {e}")
            smtp_connection.quit()
            return None
        except smtplib.SMTPException as e:
            Logger.log(2, f"Server {host}:{port} uses some weird authentication method. Error text: {e}")
            smtp_connection.quit()
            return None

    return smtp_connection


def send(message: typing.Union[MIMEMultipart, EmailMessage],
         connection: typing.Union[smtplib.SMTP, smtplib.SMTP_SSL]):
    """
    Sends the provided message through opened connection to the server
    If there is some error with message, returns False
    Otherwise returns True
    """
    Logger.log(4, f"mail.send()")
    try:
        # https://docs.python.org/3/library/smtplib.html#smtplib.SMTP.send_message
        connection.send_message(message)
    except ValueError as e:
        Logger.log(2, f"Message could not be send. Error text: {e}")
        return False

    return True


def disconnect(connection: typing.Union[smtplib.SMTP, smtplib.SMTP_SSL]):
    """
    Disconnects opened SMPT connection
    """
    Logger.log(4, f"mail.disconnect()")
    connection.quit()


def send_using_creds(message: str, html_message: str, credentials: Messaging.EmailCreds, email_info: Messaging.Email):
    Logger.log(4, f"mail.send_using_creds()")
    subject, body = _divide_to_subject_body(message)

    if not subject:
        subject = "fs2od info"

    connection = connect(
        host=credentials.smtp_server,
        port=credentials.smtp_port,
        login=credentials.login,
        password=credentials.password,
        encryption_method=credentials.encryption_method
    )

    if connection is None:
        return False

    email_message = MIMEMultipart('alternative')

    email_message['Subject'] = subject
    email_message['From'] = credentials.message_sender
    email_message['To'] = ", ".join(email_info.to)

    part = MIMEText(body, 'plain')
    email_message.attach(part)
    if html_message:
        part = MIMEText(html_message, 'html')
        email_message.attach(part)

    status = send(email_message, connection)
    disconnect(connection)
    return status
