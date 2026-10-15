"""Rekap Isian Pekerja (versi Streamlit).

Mencatat siapa yang sudah mengisi laporan pada hari Jumat (WFA) dan
menampilkan siapa yang belum. Data disimpan sebagai satu file JSON di
repositori GitHub (disarankan repositori privat terpisah). Kalau pengaturan
GitHub tidak ada, aplikasi memakai file lokal untuk uji coba.
"""
import base64
import json
import os
import uuid
from datetime import date, timedelta

import requests
import streamlit as st

st.set_page_config(page_title="Rekap Isian Pekerja", page_icon="✅", layout="centered")

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
MAKS_HARI = 731
FILE_LOKAL = os.environ.get("REKAP_DATA_FILE", "data.json")


def fmt(d: date) -> str:
    return f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]} {d.year}"


def data_kosong() -> dict:
    return {
        "pekerja": [],
        "kategori": [{"id": "k1", "nama": "Laporan harian"}],
        "libur": {},   # {"2026-10-23": "Keterangan"}
        "isian": {},   # {"2026-10-16": {"<id kategori>": ["<id pekerja>", ...]}}
    }


# ---------------------------------------------------------------- penyimpanan
class Bentrok(Exception):
    """Data di GitHub sudah berubah sejak terakhir dimuat."""


def cfg_github():
    try:
        g = st.secrets["github"]
        return {
            "token": g["token"],
            "repo": g["repo"],
            "path": g.get("path", "data.json"),
            "branch": g.get("branch", "main"),
        }
    except Exception:
        return None


def _gh_url(c):
    return f"https://api.github.com/repos/{c['repo']}/contents/{c['path']}"


def _gh_headers(c):
    return {
        "Authorization": f"Bearer {c['token']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def muat():
    """Kembalikan (data, sha). sha dipakai GitHub untuk mendeteksi bentrok."""
    c = cfg_github()
    if c:
        r = requests.get(_gh_url(c), headers=_gh_headers(c),
                         params={"ref": c["branch"]}, timeout=20)
        if r.status_code == 404:
            return data_kosong(), None
        r.raise_for_status()
        j = r.json()
        return json.loads(base64.b64decode(j["content"]).decode("utf-8")), j["sha"]
    if os.path.exists(FILE_LOKAL):
        with open(FILE_LOKAL, encoding="utf-8") as f:
            return json.load(f), None
    return data_kosong(), None


def simpan(data: dict):
    c = cfg_github()
    teks = json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True)
    if c:
        body = {
            "message": "Perbarui rekap isian",
            "content": base64.b64encode(teks.encode("utf-8")).decode("ascii"),
            "branch": c["branch"],
        }
        if st.session_state.sha:
            body["sha"] = st.session_state.sha
        r = requests.put(_gh_url(c), headers=_gh_headers(c), json=body, timeout=30)
        if r.status_code in (409, 422):
            raise Bentrok()
        r.raise_for_status()
        st.session_state.sha = r.json()["content"]["sha"]
    else:
        with open(FILE_LOKAL, "w", encoding="utf-8") as f:
            f.write(teks)


def muat_ke_sesi():
    st.session_state.data, st.session_state.sha = muat()
    for k in [k for k in st.session_state if str(k).startswith("c_")]:
        del st.session_state[k]


def commit(pesan_ok: str | None = None) -> bool:
    """Simpan st.session_state.data. Tampilkan hasilnya ke pengguna."""
    try:
        simpan(st.session_state.data)
    except Bentrok:
        muat_ke_sesi()
        st.error("Data sudah diubah orang lain. Data terbaru sudah dimuat, "
                 "silakan ulangi perubahan Anda.")
        return False
    except Exception as e:  # jaringan, token salah, dan sebagainya
        st.error(f"Gagal menyimpan: {e}")
        return False
    if pesan_ok:
        st.toast(pesan_ok, icon="✅")
    return True


# -------------------------------------------------------------------- akses
def cek_sandi():
    try:
        sandi = st.secrets["password"]
    except Exception:
        return
    if st.session_state.get("masuk"):
        return
    with st.form("login"):
        x = st.text_input("Kata sandi", type="password")
        if st.form_submit_button("Masuk"):
            if x == sandi:
                st.session_state.masuk = True
                st.rerun()
            st.error("Kata sandi salah.")
    st.stop()


cek_sandi()

if "data" not in st.session_state:
    try:
        muat_ke_sesi()
    except Exception as e:
        st.error(f"Data tidak bisa dimuat: {e}")
        st.stop()

D = st.session_state.data
for kunci, awal in data_kosong().items():
    D.setdefault(kunci, awal)


# ---------------------------------------------------------------- tanggal
def jumat_terakhir(d: date) -> date:
    return d - timedelta(days=(d.weekday() - 4) % 7)


def lompat(d: date, arah: int) -> date:
    t = d + timedelta(days=7 * arah)
    for _ in range(60):
        if t.isoformat() not in D["libur"]:
            return t
        t += timedelta(days=7 * arah)
    return d + timedelta(days=7 * arah)


def terisi(tgl: str, kid: str, pid: str) -> bool:
    return pid in D["isian"].get(tgl, {}).get(kid, [])


if "tgl_in" not in st.session_state:
    st.session_state.tgl_in = jumat_terakhir(date.today())


def cb_geser(arah):
    st.session_state.tgl_in = lompat(st.session_state.tgl_in, arah)


def cb_terakhir():
    st.session_state.tgl_in = jumat_terakhir(date.today())


def cb_pilih():
    st.session_state.tgl_in = jumat_terakhir(st.session_state.tgl_in)


# ------------------------------------------------------------------- tampilan
kiri, kanan = st.columns([4, 1])
kiri.title("Rekap Isian Pekerja")
kanan.write("")
if kanan.button("Muat ulang", help="Ambil data terbaru dari penyimpanan"):
    muat_ke_sesi()
    st.rerun()
st.caption("Catat siapa yang sudah mengisi pada hari Jumat (WFA), lihat siapa yang belum.")
if cfg_github():
    st.caption(f"Data tersimpan di GitHub: {cfg_github()['repo']}")
else:
    st.warning("Mode uji coba: data disimpan di file lokal dan bisa hilang saat aplikasi "
               "dimulai ulang. Isi pengaturan GitHub (lihat README) agar data permanen.")

tab_tgl, tab_lap, tab_kelola = st.tabs(["Per tanggal", "Belum mengisi", "Kelola"])

# --------------------------------------------------------------- per tanggal
with tab_tgl:
    if not D["pekerja"] or not D["kategori"]:
        st.info("Belum ada pekerja atau kategori. Tambahkan dulu di tab Kelola.")
    else:
        c1, c2, c3, c4 = st.columns([1, 4, 1, 3])
        c1.button("‹", key="prev", on_click=cb_geser, args=(-1,),
                  help="Jumat sebelumnya (tanggal dikecualikan dilewati)")
        c2.date_input("Tanggal (Jumat WFA)", key="tgl_in", on_change=cb_pilih,
                      format="DD/MM/YYYY")
        c3.button("›", key="next", on_click=cb_geser, args=(1,),
                  help="Jumat berikutnya (tanggal dikecualikan dilewati)")
        c4.button("Jumat terakhir", key="last", on_click=cb_terakhir)

        tgl_d = st.session_state.tgl_in
        tgl = tgl_d.isoformat()
        if tgl in D["libur"]:
            ket = D["libur"][tgl]
            st.info("Tanggal ini dikecualikan" + (f": {ket}" if ket else "")
                    + ". Tidak dihitung di tab Belum mengisi.")

        kats, pks = D["kategori"], D["pekerja"]
        belum = sum(not terisi(tgl, k["id"], p["id"]) for k in kats for p in pks)
        total = len(kats) * len(pks)
        if belum:
            st.metric(fmt(tgl_d), f"{belum} dari {total} belum terisi")
        else:
            st.success(f"Semua {total} isian sudah terisi pada {fmt(tgl_d)}.")

        with st.form(f"form_{tgl}"):
            lebar = [3] + [2] * len(kats)
            kepala = st.columns(lebar)
            kepala[0].markdown("**Pekerja**")
            for i, k in enumerate(kats):
                kepala[i + 1].markdown(f"**{k['nama']}**")
            pilihan = {}
            for p in pks:
                baris = st.columns(lebar)
                baris[0].write(p["nama"])
                for i, k in enumerate(kats):
                    pilihan[(k["id"], p["id"])] = baris[i + 1].checkbox(
                        f"{p['nama']} - {k['nama']}",
                        value=terisi(tgl, k["id"], p["id"]),
                        key=f"c_{tgl}_{k['id']}_{p['id']}",
                        label_visibility="collapsed",
                    )
            if st.form_submit_button("Simpan", type="primary"):
                baru = {}
                for (kid, pid), ya in pilihan.items():
                    if ya:
                        baru.setdefault(kid, []).append(pid)
                # pertahankan isian milik kategori atau pekerja yang sudah dihapus
                lama = D["isian"].get(tgl, {})
                aktif_k = {k["id"] for k in kats}
                aktif_p = {p["id"] for p in pks}
                for kid, daftar in lama.items():
                    sisa = [x for x in daftar if kid not in aktif_k or x not in aktif_p]
                    if sisa:
                        baru.setdefault(kid, []).extend(sisa)
                if baru:
                    D["isian"][tgl] = baru
                else:
                    D["isian"].pop(tgl, None)
                if commit("Tersimpan."):
                    st.rerun()

# -------------------------------------------------------------------- laporan
with tab_lap:
    if not D["pekerja"] or not D["kategori"]:
        st.info("Belum ada pekerja atau kategori. Tambahkan dulu di tab Kelola.")
    else:
        a, b, c = st.columns(3)
        awal_bulan = date.today().replace(day=1)
        dari = a.date_input("Dari", value=awal_bulan, key="dari", format="DD/MM/YYYY")
        sampai = b.date_input("Sampai", value=date.today(), key="sampai", format="DD/MM/YYYY")
        nama_kat = {k["id"]: k["nama"] for k in D["kategori"]}
        pilih_kat = c.selectbox("Kategori", ["Semua kategori"] + list(nama_kat.values()))
        st.caption("Hanya menghitung hari Jumat. Tanggal yang dikecualikan dilewati.")

        if dari > sampai:
            st.error("Tanggal awal harus sebelum tanggal akhir.")
        elif (sampai - dari).days + 1 > MAKS_HARI:
            st.error("Rentang maksimal 2 tahun (731 hari).")
        else:
            kats = [k for k in D["kategori"]
                    if pilih_kat == "Semua kategori" or k["nama"] == pilih_kat]
            banyak = len(kats) > 1
            per = {}      # id pekerja -> daftar (tanggal, nama kategori)
            tanggal_hitung = set()
            d = dari
            while d <= sampai:
                t = d.isoformat()
                if d.weekday() == 4 and t not in D["libur"]:
                    for k in kats:
                        for p in D["pekerja"]:
                            if not terisi(t, k["id"], p["id"]):
                                per.setdefault(p["id"], []).append((d, k["nama"]))
                                tanggal_hitung.add(t)
                d += timedelta(days=1)

            urut = sorted((p for p in D["pekerja"] if p["id"] in per),
                          key=lambda p: -len(per[p["id"]]))
            if not urut:
                st.success("Tidak ada yang belum mengisi pada rentang ini.")
            else:
                jumlah = sum(len(v) for v in per.values())
                st.metric("Pekerja yang belum mengisi", len(urut),
                          f"{jumlah} isian di {len(tanggal_hitung)} tanggal",
                          delta_color="off")

                def label(x):
                    return fmt(x[0]) + (f" ({x[1]})" if banyak else "")

                for p in urut:
                    with st.container(border=True):
                        st.markdown(f"**{p['nama']}** · {len(per[p['id']])} tanggal")
                        st.write(" • ".join(label(x) for x in per[p["id"]]))
                teks = "\n".join(
                    f"{p['nama']} belum mengisi: " + "; ".join(label(x) for x in per[p["id"]])
                    for p in urut)
                st.caption("Teks untuk disalin (tombol salin ada di pojok kanan atas kotak):")
                st.code(teks, language=None)

# ----------------------------------------------------------------------- kelola
def kelola_daftar(judul: str, kunci: str, hint: str):
    with st.container(border=True):
        st.subheader(judul)
        st.caption(hint)
        daftar = D[kunci]
        if daftar:
            for x in daftar:
                st.write("• " + x["nama"])
        else:
            st.write("Belum ada.")

        with st.form(f"tambah_{kunci}", clear_on_submit=True):
            nama = st.text_input("Nama baru")
            if st.form_submit_button("Tambah"):
                nama = nama.strip()
                if not nama:
                    st.error("Nama tidak boleh kosong.")
                elif any(x["nama"].lower() == nama.lower() for x in daftar):
                    st.error("Nama itu sudah ada.")
                else:
                    daftar.append({"id": uuid.uuid4().hex[:8], "nama": nama})
                    if commit("Ditambahkan."):
                        st.rerun()

        if daftar:
            opsi = {x["id"]: x["nama"] for x in daftar}
            with st.form(f"ubah_{kunci}"):
                pid = st.selectbox("Pilih untuk diubah atau dihapus", list(opsi),
                                   format_func=lambda i: opsi[i])
                baru = st.text_input("Nama baru (untuk Ubah nama)")
                yakin = st.checkbox("Ya, hapus yang dipilih (untuk Hapus)")
                k1, k2 = st.columns(2)
                ubah = k1.form_submit_button("Ubah nama")
                hapus = k2.form_submit_button("Hapus")
                if ubah:
                    baru = baru.strip()
                    if not baru:
                        st.error("Isi nama baru dulu.")
                    elif any(x["id"] != pid and x["nama"].lower() == baru.lower() for x in daftar):
                        st.error("Nama itu sudah ada.")
                    else:
                        for x in daftar:
                            if x["id"] == pid:
                                x["nama"] = baru
                        if commit("Nama diubah."):
                            st.rerun()
                if hapus:
                    if not yakin:
                        st.error("Centang dulu \"Ya, hapus\" untuk menghapus.")
                    else:
                        D[kunci] = [x for x in daftar if x["id"] != pid]
                        if commit("Dihapus."):
                            st.rerun()


with tab_kelola:
    kelola_daftar("Pekerja", "pekerja", "Orang yang wajib mengisi.")
    kelola_daftar("Kategori", "kategori", "Jenis isian, misalnya laporan harian.")

    with st.container(border=True):
        st.subheader("Tanggal dikecualikan")
        st.caption("Tanggal merah atau hari lain yang tidak perlu diisi. "
                   "Tidak dihitung sebagai belum mengisi.")
        if D["libur"]:
            for t in sorted(D["libur"]):
                ket = D["libur"][t]
                st.write("• " + fmt(date.fromisoformat(t)) + (f" · {ket}" if ket else ""))
        else:
            st.write("Belum ada.")
        with st.form("tambah_libur", clear_on_submit=True):
            l1, l2 = st.columns([2, 3])
            tl = l1.date_input("Tanggal", value=jumat_terakhir(date.today()), format="DD/MM/YYYY")
            kl = l2.text_input("Keterangan (boleh kosong)", placeholder="Contoh: Hari Raya")
            if st.form_submit_button("Tambah"):
                D["libur"][tl.isoformat()] = kl.strip()
                if commit("Ditambahkan."):
                    st.rerun()
        if D["libur"]:
            with st.form("hapus_libur"):
                hapus_t = st.multiselect("Hapus tanggal", sorted(D["libur"]),
                                         format_func=lambda t: fmt(date.fromisoformat(t)))
                if st.form_submit_button("Hapus yang dipilih"):
                    for t in hapus_t:
                        D["libur"].pop(t, None)
                    if hapus_t and commit("Dihapus."):
                        st.rerun()

    st.caption("Menghapus pekerja atau kategori menyembunyikannya dari rekap. "
               "Riwayat isiannya tetap tersimpan di file data.")
