from fastapi.testclient import TestClient

from backend.main import app


def test_registracija_uspe():
    odgovor = TestClient(app).post(
        "/register", json={"name": "Ana", "email": "ana@test.si", "password": "geslo", "role": "buyer"}
    )
    assert odgovor.status_code == 201


def test_registracija_z_obstojeco_eposto_ne_uspe():
    odjemalec = TestClient(app)
    podatki = {"name": "Ana", "email": "ana@test.si", "password": "geslo", "role": "buyer"}
    odjemalec.post("/register", json=podatki)
    odgovor = odjemalec.post("/register", json=podatki)
    assert odgovor.status_code == 409
    assert odgovor.json()["detail"] == "Račun s tem e-poštnim naslovom že obstaja"


def test_registracija_kot_administrator_ni_mogoca():
    odgovor = TestClient(app).post(
        "/register", json={"name": "Ana", "email": "ana@test.si", "password": "geslo", "role": "admin"}
    )
    assert odgovor.status_code == 422


def test_prijava_z_napacnim_geslom(kupec):
    odgovor = TestClient(app).post("/login", json={"email": "kupec@test.si", "password": "napacno"})
    assert odgovor.status_code == 401
    assert odgovor.json()["detail"] == "Napačna e-pošta ali geslo"


def test_prijava_in_odjava(kupec):
    assert kupec.get("/me").json() == {"name": "kupec", "role": "buyer"}
    kupec.post("/logout")
    assert kupec.get("/me").json() is None
    assert kupec.get("/my/searches").status_code == 401


def test_zamenjava_vloge(kupec):
    odgovor = kupec.put("/me/role", json={"role": "seller"})
    assert odgovor.json()["role"] == "seller"
    assert kupec.get("/my/listings").status_code == 200
    assert kupec.get("/my/searches").status_code == 403


def test_zamenjava_vloge_v_administratorja_ni_mogoca(kupec):
    assert kupec.put("/me/role", json={"role": "admin"}).status_code == 422
