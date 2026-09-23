from pathlib import Path


def login(client):
    return client.post(
        "/login",
        data={"email": "admin@example.invalid", "password": "senha-de-teste-sem-segredo"},
    )


def test_header_contains_sound_control_and_mp3(client):
    login(client)
    response = client.get("/")

    assert response.status_code == 200
    assert b"data-alert-sound-toggle" in response.data
    assert b"data-system-alert-audio" in response.data
    assert b"audio/alarme_sistema.mp3" in response.data


def test_operational_pages_mark_alerts_as_audible(client):
    login(client)

    for path in ("/", "/rotas", "/frota", "/relatorios", "/relatorios/frota", "/relatorios/rotas"):
        response = client.get(path)
        assert response.status_code == 200
        assert b"data-audible-alert" in response.data
        assert b"data-alert-id" in response.data


def test_alert_audio_asset_is_valid_mp3():
    audio = Path("uairotas/static/audio/alarme_sistema.mp3")

    assert audio.exists()
    assert audio.stat().st_size > 100_000
    header = audio.read_bytes()[:3]
    assert header == b"ID3" or header[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"}


def test_alert_javascript_supports_preferences_autoplay_fallback_and_realtime_events():
    script = Path("uairotas/static/js/app.js").read_text(encoding="utf-8")

    assert '"uairotas-alert-sound"' in script
    assert '"uairotas-heard-alerts"' in script
    assert "systemAlertAudio.play()" in script
    assert "systemAlertAudio.pause()" in script
    assert 'window.addEventListener("uairotas:alert"' in script
    assert "sessionStorage" in script
    assert "needs-interaction" in script


def test_error_flash_is_marked_for_sound(client):
    login(client)
    response = client.post("/frota/registros/veiculo", data={}, follow_redirects=True)

    assert response.status_code == 200
    assert b'data-alert-id="fleet-form-error"' in response.data
