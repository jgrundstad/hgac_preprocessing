import mandrill


html_style = '''
<STYLE>
h1 {font-size:'12px';}
h2 {font-size:'11px';}
th {
    font-family:courier;
    font-size:12px;
    background-color:7D0000;
    color:white;
}
td {
    font-family:courier;
    font-size:10px;
    white-space:nowrap;
    text-align:right;
}
</STYLE>
'''


def send_mail(api_key=None, to=None, cc=None, reply_to=None, subject=None,
              content=None, html_files=None):
    """

    :param api_key:
    :param to: list of email address strings
    :param cc: list of email address strings
    :param reply_to: email address string
    :param content: string
    :param html_files: list of files containing html
    :param subject:
    :return:
    """
    print "Emailer sending this in content: {}".format(content)
    mandrill_client = mandrill.Mandrill(api_key)
    message = {
        "to": [],
        "global_merge_vars": [],
        "subject": subject,
    }
    if to:
        for address in to:
            message['to'].append({"email": address, "type": "to"})

    if cc:
        for address in cc:
            message['to'].append({"email": address, "type": "cc"})

    if reply_to:
        message['from_email'] = reply_to
        #message['text'] = content

    html_content = ''
    if html_files:
        for filename in html_files:
            print "emailing demultiplex summary file: {}".format(filename)
            with open(filename, 'r') as f:
                html_content += f.read()

    content = content.replace('\n', '<br>\n')

    message['html'] = '<br>\n'.join([content, html_content, html_style])

    result = mandrill_client.messages.send(message=message, async=False,
                                           ip_pool='Main Pool')
    print "Sent email via mandrill:\n{}".format(result)
