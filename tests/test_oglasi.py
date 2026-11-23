def test_oglas_lahko_odda_samo_prodajalec(kupec):
    odgovor = kupec.post("/listings", json={"set_id": 1, "condition": "new", "price": "50"})
    assert odgovor.status_code == 403


def test_oglas_z_neveljavno_ceno_ni_oddan(prodajalec):
    for cena in ["0", "-5", "12.345"]:
        odgovor = prodajalec.post("/listings", json={"set_id": 1, "condition": "new", "price": cena})
        assert odgovor.status_code == 422


def test_oglas_za_komplet_izven_kataloga(prodajalec):
    odgovor = prodajalec.post("/listings", json={"set_id": 999, "condition": "new", "price": "50"})
    assert odgovor.status_code == 404


def test_oddan_oglas_caka_na_pregled(prodajalec, admin):
    odgovor = prodajalec.post("/listings", json={"set_id": 1, "condition": "used", "price": "20.50"})
    assert odgovor.json()["status"] == "pending"
    assert prodajalec.get("/listings").json() == []
    assert len(admin.get("/admin/listings").json()) == 1


def test_odobren_oglas_je_objavljen(prodajalec, objavljen_oglas):
    objavljeni = prodajalec.get("/listings").json()
    assert [o["id"] for o in objavljeni] == [objavljen_oglas]


def test_zavrnitev_brez_razloga_ni_mogoca(prodajalec, admin):
    oglas = prodajalec.post("/listings", json={"set_id": 1, "condition": "new", "price": "50"}).json()
    assert admin.post(f"/listings/{oglas['id']}/reject", json={"reason": ""}).status_code == 422


def test_zavrnjenega_oglasa_ni_mogoce_odobriti(prodajalec, admin):
    oglas = prodajalec.post("/listings", json={"set_id": 1, "condition": "new", "price": "50"}).json()
    admin.post(f"/listings/{oglas['id']}/reject", json={"reason": "Slaba slika"})
    assert admin.post(f"/listings/{oglas['id']}/approve").status_code == 409
    moji = prodajalec.get("/my/listings").json()
    assert moji[0]["status"] == "rejected"
    assert moji[0]["rejection_reason"] == "Slaba slika"


def test_rezervacija_prikaze_kontakt_prodajalca(kupec, objavljen_oglas):
    odgovor = kupec.post(f"/listings/{objavljen_oglas}/reserve")
    assert odgovor.status_code == 200
    assert odgovor.json()["seller_email"] == "prodajalec@test.si"
    assert kupec.get("/listings").json() == []


def test_ze_rezerviranega_oglasa_ni_mogoce_rezervirati(kupec, objavljen_oglas):
    kupec.post(f"/listings/{objavljen_oglas}/reserve")
    odgovor = kupec.post(f"/listings/{objavljen_oglas}/reserve")
    assert odgovor.status_code == 409
    assert odgovor.json()["detail"] == "Oglas ni več na voljo"


def test_lastnega_oglasa_ni_mogoce_rezervirati(prodajalec, objavljen_oglas):
    prodajalec.put("/me/role", json={"role": "buyer"})
    assert prodajalec.post(f"/listings/{objavljen_oglas}/reserve").status_code == 403


def test_sprostitev_rezervacije(prodajalec, kupec, objavljen_oglas):
    kupec.post(f"/listings/{objavljen_oglas}/reserve")
    assert prodajalec.post(f"/listings/{objavljen_oglas}/release").status_code == 200
    moj = prodajalec.get("/my/listings").json()[0]
    assert moj["status"] == "approved"
    assert moj["buyer_email"] is None


def test_prodajo_potrdi_samo_lastnik_oglasa(kupec, admin, objavljen_oglas):
    kupec.post(f"/listings/{objavljen_oglas}/reserve")
    assert admin.post(f"/listings/{objavljen_oglas}/sell").status_code == 403
    kupec.put("/me/role", json={"role": "seller"})
    assert kupec.post(f"/listings/{objavljen_oglas}/sell").status_code == 409
