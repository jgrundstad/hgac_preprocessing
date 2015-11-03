import mandrill


def send_mail(api_key=None, to=None, cc=None, reply_to=None, subject=None, content=None):
    """

    :param api_key:
    :param to: list of email address strings
    :param cc: list of email address strings
    :param reply_to: email address string
    :param content: string
    :return:
    """
    mandrill_client = mandrill.Mandrill(api_key)
    message = {
        "to": [],
        "global_merge_vars": [],
        "subject": subject,
    }
    for address in to:
        message['to'].append({"email": address, "type": "to"})

    for address in cc:
        message['to'].append({"email": address, "type": "cc"})

    message['from_email'] = reply_to
    message['text'] = content
    result = mandrill_client.messages.send(message=message, async=False,
                                           ip_pool='Main Pool')
    print "Sent email via mandrill:\n{}".format(result)