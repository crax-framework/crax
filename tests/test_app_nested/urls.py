from crax.urls import Route, Url, include

from .routers import (
    TestGetParams,
    TestGetParamsRegex,
    TestMissedTemplate,
    TestNotFoundTemplate,
    TestInnerTemplateExceptions,
    TestJSONView,
    TestSendCookiesBack,
    TestSetCookies,
    TestEmptyMethods,
    TestMasquerade,
    TestMasqueradeNoScope,
    TestUrlCreation,
)

url_list = [
    Route(urls=(Url("/test_json_view")), handler=TestJSONView),
    Route(urls=(Url("/test_send_cookies_back")), handler=TestSendCookiesBack),
    Route(urls=(Url("/test_set_cookies")), handler=TestSetCookies),
    Route(urls=(Url("/test_masquerade/", masquerade=True)), handler=TestMasquerade),
    Route(
        urls=(Url("/masquerade_no_scope/", masquerade=True)),
        handler=TestMasqueradeNoScope,
    ),
    Route(
        urls=(
            Url("/test_param/<param_1>/<param_2>/", name="test_param"),
            Url("/test_param"),
        ),
        handler=TestGetParams,
    ),
    Route(urls=(Url("/test_create_url")), handler=TestUrlCreation),
    Route(urls=(Url("/test_missed_template")), handler=TestMissedTemplate),
    Route(urls=(Url("/test_not_found_template")), handler=TestNotFoundTemplate),
    Route(urls=(Url("/inner_template_ex")), handler=TestInnerTemplateExceptions),
    Route(urls=(Url("/test_empty_method")), handler=TestEmptyMethods),
    Route(
        urls=(
            Url(
                r"/test_param_regex/(?P<param_1>\w{0,30})/(?P<param_2>\w{0,30})/",
                type="re_path",
            )
        ),
        handler=TestGetParamsRegex,
    ),
]
