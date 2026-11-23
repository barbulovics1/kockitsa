def test_iskanje_brez_stanja_ni_shranjeno(kupec):
    odgovor = kupec.post("/searches", json={"set_id": 1, "max_price": "60", "conditions": []})
    assert odgovor.status_code == 422


def test_samo_eno_aktivno_iskanje_na_komplet(kupec):
    iskanje = {"set_id": 1, "max_price": "60", "conditions": ["new"]}
    assert kupec.post("/searches", json=iskanje).status_code == 201
    odgovor = kupec.post("/searches", json=iskanje)
    assert odgovor.status_code == 409
    assert odgovor.json()["detail"] == "Za ta komplet že imate aktivno iskanje"


def test_ujemajoci_oglasi_upostevajo_ceno_in_stanje(kupec, objavljen_oglas):
    kupec.post("/searches", json={"set_id": 1, "max_price": "60", "conditions": ["new"]})
    kupec.post("/searches", json={"set_id": 2, "max_price": "60", "conditions": ["new"]})
    iskanja = {i["set_name"]: i for i in kupec.get("/my/searches").json()}
    assert [o["id"] for o in iskanja["Galaxy Explorer"]["matches"]] == [objavljen_oglas]
    assert iskanja["Medieval Castle"]["matches"] == []
    assert kupec.get("/my/searches/count").json()["count"] == 1


def test_predrag_oglas_ni_ujemajoc(kupec, objavljen_oglas):
    kupec.post("/searches", json={"set_id": 1, "max_price": "40", "conditions": ["new", "used"]})
    assert kupec.get("/my/searches").json()[0]["matches"] == []
    assert kupec.get("/my/searches/count").json()["count"] == 0


def test_iskanje_se_ob_nakupu_zakljuci(prodajalec, kupec, objavljen_oglas):
    kupec.post("/searches", json={"set_id": 1, "max_price": "60", "conditions": ["new"]})
    kupec.post(f"/listings/{objavljen_oglas}/reserve")
    assert prodajalec.post(f"/listings/{objavljen_oglas}/sell").status_code == 200
    assert kupec.get("/my/searches").json()[0]["status"] == "fulfilled"


def test_brisanje_iskanja(kupec):
    iskanje = kupec.post("/searches", json={"set_id": 1, "max_price": "60", "conditions": ["new"]}).json()
    assert kupec.delete(f"/searches/{iskanje['id']}").status_code == 200
    assert kupec.get("/my/searches").json() == []
