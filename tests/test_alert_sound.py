import re
import hashlib
from pathlib import Path
from uairotas.analytics import active_alerts
from uairotas.models import AlertAcknowledgement

def test_original_sound_preserved_and_loaded_on_demand(authenticated):
    path=Path("uairotas/static/audio/alarme_sistema.mp3")
    assert len(path.read_bytes())==304128
    assert hashlib.sha256(path.read_bytes()).hexdigest()=="9dbd60f923d88fc74d2903edebebae2aaeb99ce1edf9feff0dfd2f76ce205221"
    page=authenticated.get("/")
    assert b'preload="none"' in page.data and b"data-sound-volume" in page.data and b"data-sound-test" in page.data

def test_same_event_id_across_pages_acknowledgement_keeps_visual(app,authenticated,demo):
    with app.app_context(): event=next(a for a in active_alerts(1) if a["id"].startswith("lunch:"))
    for path in ["/","/rotas","/alertas"]:
        response=authenticated.get(path)
        assert f'data-alert-id="{event["id"]}"'.encode() in response.data
    assert authenticated.post("/alertas/reconhecer",data={"occurrence_id":event["id"]}).status_code==302
    response=authenticated.get("/alertas")
    tag=re.search(r'<article[^>]*data-alert-id="'+re.escape(event["id"])+r'"[^>]*>',response.text).group(0)
    assert "data-audible-alert" not in tag and "Visto por você".encode() in response.data
    with app.app_context(): assert AlertAcknowledgement.query.count()==1
    assert authenticated.post("/alertas/reconhecer",data={"occurrence_id":event["id"]}).status_code==302

def test_different_form_errors_have_new_occurrence_ids(authenticated):
    pages=[authenticated.post("/frota/registros/veiculo",data={}).text for _ in range(2)]
    ids=[re.search(r'data-alert-id="(form:[^"]+)"',p).group(1) for p in pages]
    assert ids[0]!=ids[1]
    assert authenticated.post("/alertas/reconhecer",data={"occurrence_id":"not-real"}).status_code==400
