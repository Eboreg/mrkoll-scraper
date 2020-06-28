from mrks.scraper import generate_rss


def application(environ, start_response):
    # http://wsgi.tutorial.codepoint.net/application-interface
    # https://www.toptal.com/python/pythons-wsgi-server-application-interface

    if environ.get("REQUEST_METHOD").upper() == "HEAD":
        start_response("200 OK", [])
        return []

    rss = generate_rss()
    response_headers = [
        ("Content-Type", "application/rss+xml; charset=utf-8"),
        ("Content-Length", str(len(rss))),
    ]

    start_response("200 OK", response_headers)
    return [rss]
