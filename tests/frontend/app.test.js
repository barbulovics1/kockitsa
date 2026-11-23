import { readFileSync } from "node:fs";
import { describe, expect, test, vi } from "vitest";

const PREDLOGA = readFileSync("frontend/index.html", "utf8");

// app.js ob nalaganju pokliče /me in izriše glavo strani; odgovore backenda nadomestimo s testnimi
async function naloziStran(odgovori, { stran = "index.html", vloge, prijava = false } = {}) {
    document.documentElement.innerHTML = PREDLOGA.replace(/<script[\s\S]*?<\/script>/g, "");
    if (vloge) document.body.dataset.role = vloge;
    if (prijava) document.body.dataset.login = "";
    window.history.replaceState({}, "", `/${stran}`);
    global.fetch = vi.fn(async (url) => {
        const [status, data] = odgovori[url] ?? [404, { detail: "Ni najdeno" }];
        return { ok: status < 400, json: async () => data };
    });
    vi.resetModules();
    await import("../../frontend/app.js");
    await vi.waitFor(() => expect(document.querySelector("#header .bar")).not.toBeNull());
}

const besedilaMenija = () => [...document.querySelectorAll("#header nav a")].map((a) => a.textContent);

describe("glava strani", () => {
    test("neprijavljen uporabnik vidi povezavi za prijavo in registracijo", async () => {
        await naloziStran({ "/me": [200, null] });
        const povezave = [...document.querySelectorAll("#header .user a")].map((a) => a.textContent);
        expect(povezave).toEqual(["Prijava", "Registracija"]);
        expect(besedilaMenija()).toEqual([]);
    });

    test("prodajalec vidi svoj meni ter ime in vlogo", async () => {
        await naloziStran({ "/me": [200, { name: "Miha", role: "seller" }] });
        expect(besedilaMenija()).toEqual(["Oglasi", "Oddaj oglas", "Moji oglasi", "Profil"]);
        expect(document.querySelector("#header .user span").textContent).toBe("Miha (prodajalec)");
    });

    test("administrator vidi samo oglase v pregledu", async () => {
        await naloziStran({ "/me": [200, { name: "Admin", role: "admin" }] });
        expect(besedilaMenija()).toEqual(["Oglasi v pregledu"]);
    });

    test("kupec v meniju vidi število iskanj z ujemajočimi oglasi", async () => {
        await naloziStran({
            "/me": [200, { name: "Ana", role: "buyer" }],
            "/my/searches/count": [200, { count: 2 }],
        });
        await vi.waitFor(() => expect(besedilaMenija()).toContain("Moja iskanja (2)"));
    });

    test("kupec brez ujemajočih oglasov nima števca v meniju", async () => {
        await naloziStran({
            "/me": [200, { name: "Ana", role: "buyer" }],
            "/my/searches/count": [200, { count: 0 }],
        });
        expect(besedilaMenija()).toEqual(["Oglasi", "Moja iskanja", "Profil"]);
    });

    test("trenutna stran je v meniju označena kot aktivna", async () => {
        await naloziStran({ "/me": [200, { name: "Miha", role: "seller" }] }, { stran: "oddaj.html" });
        expect(document.querySelector("#header nav a.active").textContent).toBe("Oddaj oglas");
    });
});
