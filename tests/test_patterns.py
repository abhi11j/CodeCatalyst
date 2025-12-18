from Scanner.Utils.singleton import Singleton
from Scanner.GitHub.GitHubClient import GitHubClient
from Scanner.GitHub.ProviderFactory import ProviderFactory
from Scanner.Events.event_dispatcher import EventDispatcher
from Scanner.GitHub.Implementation.AutomatedSuggestion import AutomatedSuggestion


def test_singleton_githubclient():
    c1 = GitHubClient(token=None)
    c2 = GitHubClient(token=None)
    assert c1 is c2


def test_provider_factory_register_and_create():
    # register a temporary provider
    ProviderFactory.register("tmp", lambda: AutomatedSuggestion())
    prov = ProviderFactory.create("tmp")
    assert isinstance(prov, AutomatedSuggestion)


def test_event_dispatcher_subscribe_dispatch():
    disp = EventDispatcher()
    events = []

    def on_scan_started(**kwargs):
        events.append(("started", kwargs.get("target")))

    disp.subscribe("scan_started", on_scan_started)
    disp.dispatch("scan_started", target="owner/repo")
    assert events == [("started", "owner/repo")]
