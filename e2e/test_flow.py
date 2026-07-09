import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8000"


def test_home_page_loads(page: Page):
    """Test home page loads correctly."""
    page.goto(BASE_URL)
    expect(page).to_have_title("Meeting Mind")
    expect(page.locator("h1")).to_contain_text("Meeting Mind")


def test_form_elements_present(page: Page):
    """Test all form elements are present on home page."""
    page.goto(BASE_URL)
    expect(page.locator("#meeting-title")).to_be_visible()
    expect(page.locator("#transcript")).to_be_visible()
    expect(page.locator("#submit-btn")).to_be_visible()


def test_empty_transcript_shows_error(page: Page):
    """Test submitting empty transcript shows error."""
    page.goto(BASE_URL)
    page.click("#submit-btn")
    expect(page.locator("#error-msg")).to_be_visible()
    expect(page.locator("#error-msg")).to_contain_text("Please paste a meeting transcript")


def test_short_transcript_shows_error(page: Page):
    """Test submitting short transcript shows error."""
    page.goto(BASE_URL)
    page.fill("#transcript", "Too short")
    page.click("#submit-btn")
    expect(page.locator("#error-msg")).to_be_visible()


def test_valid_submission_shows_status_card(page: Page):
    """Test valid submission shows status card."""
    page.goto(BASE_URL)
    page.fill("#meeting-title", "Test Meeting")
    page.fill("#transcript", """
        John: We need to update the login page by Friday.
        Sarah: I can handle the backend changes.
        Mike: I will fix the payment bug by Wednesday.
        Sarah: The third party API is unstable, that is a risk.
        John: Good point. Mike can you also write the tests by end of sprint?
    """)
    page.click("#submit-btn")
    expect(page.locator("#status-card")).to_be_visible()
    expect(page.locator("#status-title")).to_contain_text("Test Meeting")


def test_past_meetings_section_present(page: Page):
    """Test past meetings section is present."""
    page.goto(BASE_URL)
    expect(page.locator("text=Past Meetings")).to_be_visible()


def test_health_endpoint(page: Page):
    """Test health endpoint returns ok."""
    page.goto(f"{BASE_URL}/health")
    expect(page.locator("body")).to_contain_text("ok")