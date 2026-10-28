"""Rekap Isian Pekerja (versi Streamlit).

Mencatat siapa yang sudah mengisi laporan pada hari Jumat (WFA) dan
menampilkan siapa yang belum. Data disimpan sebagai satu file JSON di
repositori GitHub (disarankan repositori privat terpisah). Kalau pengaturan
GitHub tidak ada, aplikasi memakai file lokal untuk uji coba.
"""
import base64
import copy
import html
import json
import os
import uuid
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Rekap Isian Pekerja", page_icon="📋", layout="wide")

st.markdown("""
<style>
.block-container{padding:3.4rem 2rem 4rem;max-width:1600px}
.eyebrow{font-size:.72rem;font-weight:700;letter-spacing:.09em;color:#2b7a57}
.judul-hal{font-size:1.6rem;font-weight:700;color:#111827;margin:.1rem 0 1rem}
[data-testid="stSidebar"]{background:#0b1220}
[data-testid="stSidebar"] *{color:#e5e7eb}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *{color:#94a3b8}
.brand{display:flex;align-items:center;gap:.7rem;padding:.3rem .2rem 1.1rem;border-bottom:1px solid rgba(255,255,255,.08);margin-bottom:.4rem}
.brand .b1{font-weight:700;font-size:1.05rem;color:#fff;line-height:1.2}
.brand .b2{font-size:.76rem;color:#94a3b8;margin-top:.1rem}
.sp{height:1.2rem}
.grup{font-size:.66rem;font-weight:700;letter-spacing:.12em;color:#64748b;margin:1rem 0 .35rem .3rem}
[data-testid="stSidebar"] [data-testid="stExpander"]{background:transparent;border:0;box-shadow:none;margin-bottom:.2rem}
[data-testid="stSidebar"] [data-testid="stExpander"] details{border:0}
[data-testid="stSidebar"] [data-testid="stExpander"] summary{font-weight:600;font-size:.92rem;padding:.55rem .5rem;border-radius:8px}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover{background:rgba(255,255,255,.05)}
[data-testid="stSidebar"] [data-testid="stExpanderDetails"]{padding:.1rem 0 .3rem .5rem;border-left:1px solid rgba(255,255,255,.1);margin-left:1rem}
[class*="st-key-nav_"] button{justify-content:flex-start !important;text-align:left !important;border:0 !important;
  border-radius:8px;min-height:2.4rem;background:transparent !important;color:#cbd5e1 !important;
  font-weight:500;font-size:.9rem;box-shadow:inset 3px 0 0 transparent}
[class*="st-key-nav_"] button:hover{background:rgba(255,255,255,.06) !important;color:#fff !important}
[class*="st-key-nav_"] button[kind="primary"]{background:rgba(52,168,116,.18) !important;color:#fff !important;
  font-weight:600;box-shadow:inset 3px 0 0 #34d399}
[class*="st-key-nav_"] button > div,[class*="st-key-nav_"] button [data-testid="stMarkdownContainer"],
[class*="st-key-nav_"] button p{text-align:left !important;justify-content:flex-start !important}
[class*="st-key-nav_muat"] button{border:1px solid rgba(255,255,255,.12) !important;justify-content:center !important}
.st-key-kartu_filter,.st-key-kartu_filter_tw,.st-key-kartu_tabel,.st-key-kartu_pegawai,[class*="st-key-kartu_g"]{background:#fff;border:1px solid #e3e7ee;border-radius:16px;
  padding:1.1rem 1.2rem;box-shadow:0 1px 3px rgba(16,24,40,.06);margin-bottom:.9rem}
[data-testid="stExpander"]{background:#fff;border-radius:14px !important;box-shadow:0 1px 3px rgba(16,24,40,.06)}
.statcard{display:flex;flex-wrap:wrap;background:#fff;border:1px solid #e3e7ee;border-radius:16px;
  box-shadow:0 1px 3px rgba(16,24,40,.06);margin:.2rem 0 .6rem;overflow:hidden}
.sc-kiri{flex:2 1 280px;padding:1rem 1.2rem}
.sc-judul{font-size:1.35rem;font-weight:800;color:#111827;margin-top:.5rem}
.sc-ket{font-size:.85rem;color:#6b7280;margin-top:.15rem}
.tag{display:inline-block;background:#e8f3ec;color:#1f6b49;font-size:.72rem;font-weight:700;border-radius:999px;
  padding:.15rem .65rem;margin-right:.4rem}
.tag-m{background:#fff4d6;color:#8a5a00}
.sc-stat{flex:1 1 90px;border-left:1px solid #eef0f4;text-align:center;padding:1rem .4rem}
.sc-lab{font-size:.7rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#6b7280}
.sc-val{font-size:1.7rem;font-weight:800;color:#111827;margin-top:.2rem}
.sc-val.g{color:#166534}.sc-val.m{color:#b42318}
[data-testid="stMetric"]{border:1px solid #d9dee7;border-radius:8px;padding:.8rem 1rem;
  background:#fff}
[data-testid="stForm"]{border-radius:8px;border-color:#d9dee7;background:#fff}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:8px}
.nama{font-weight:650;font-size:1.02rem;margin-bottom:.35rem}
.jml{font-weight:400;opacity:.65;font-size:.88rem}
.chip{display:inline-block;margin:.15rem .4rem .15rem 0;padding:.12rem .7rem;border-radius:999px;
  background:#fde8e6;color:#b42318;font-size:.86rem;font-weight:500;white-space:nowrap}
[class*="st-key-chip_"],[class*="st-key-chip_"] [data-testid="stButton"]{width:auto}
[class*="st-key-chip_"] button{min-height:0;padding:.12rem .7rem;border:0 !important;border-radius:999px;
  background:#fde8e6 !important;color:#b42318 !important;font-size:.86rem;font-weight:500}
[class*="st-key-chip_"] button:hover{filter:brightness(.93)}
[data-testid="InputInstructions"]{display:none}
.thead-s{background:#256b4a;color:#fff;font-weight:650;font-size:.7rem;letter-spacing:.03em;text-transform:uppercase;text-align:center;padding:.5rem .25rem;border-radius:4px;min-height:2.6rem;display:flex;align-items:center;justify-content:center}
.thead{background:#256b4a;color:#fff;font-weight:650;padding:.55rem .7rem;border-radius:4px;font-size:.9rem}
[class*="st-key-thead_"],[class*="st-key-thead_"] [data-testid="stButton"]{width:100%}
[class*="st-key-thead_"] button{width:100%;background:#256b4a !important;color:#fff !important;border:0 !important;
  font-weight:650;border-radius:4px;min-height:2.4rem;padding:.2rem .3rem;white-space:nowrap}
[class*="st-key-thead_"] button:hover{filter:brightness(.92)}
[class*="st-key-pgedit_"] button,[class*="st-key-pghapus_"] button{min-height:2rem;padding:.1rem .5rem;border:0 !important;color:#fff !important}
[class*="st-key-pgedit_"] button{background:#2f5d9e !important}
[class*="st-key-pghapus_"] button{background:#b42318 !important}
.ket{opacity:.7;font-size:.9rem}
.garis{border-top:1px solid #e3e7ee;margin:.3rem 0}
.peg{font-weight:650}
.nip{font-size:.85rem;color:#5b6573;font-variant-numeric:tabular-nums}
[class*="st-key-cell_"],[class*="st-key-cell_"] [data-testid="stButton"]{width:100%}
[class*="st-key-cell_"] button{width:100%;border:0 !important;font-weight:600;min-height:2.6rem}
[class*="st-key-cell_belum_"] button{background:#fde8e6 !important;color:#b42318 !important}
[class*="st-key-cell_sudah_"] button{background:#dcf3e4 !important;color:#166534 !important}
[class*="st-key-cell_"] button:hover{filter:brightness(.95)}
@media (max-width: 640px){
  [data-testid="stHorizontalBlock"]:has([class*="st-key-cell_"]),
  [data-testid="stHorizontalBlock"]:has([class*="st-key-all_"]){flex-wrap:nowrap !important;gap:.5rem !important}
  [data-testid="stHorizontalBlock"]:has([class*="st-key-cell_"]) > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:has([class*="st-key-all_"]) > [data-testid="stColumn"]{min-width:0 !important}
  [class*="st-key-cell_"] button{font-size:.85rem;padding:.25rem .4rem}
  [class*="st-key-all_"] button{font-size:.75rem;padding:.2rem .4rem}
}
.bidang{font-weight:700;font-size:.78rem;text-transform:uppercase;letter-spacing:.07em;color:#256b4a;background:#e8f3ec;border-left:3px solid #256b4a;padding:.35rem .7rem;border-radius:4px;margin:1rem 0 .4rem}
</style>
""", unsafe_allow_html=True)

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
MAKS_HARI = 731
AWAL_WFA = date(2026, 2, 13)   # Jumat pertama WFA, tanggal awal bawaan di laporan
# Pilihan di formulir pegawai. Ubah daftar ini kalau sebutan di instansi Anda berbeda.
GOLONGAN = ["I/a", "I/b", "I/c", "I/d", "II/a", "II/b", "II/c", "II/d",
            "III/a", "III/b", "III/c", "III/d", "IV/a", "IV/b", "IV/c", "IV/d", "IV/e"]
GOLONGAN_PPPK = ["PPPK " + r for r in (
    "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII".split())]
GOLONGAN += GOLONGAN_PPPK
PANGKAT = {"I/a": "Juru Muda", "I/b": "Juru Muda Tingkat I", "I/c": "Juru", "I/d": "Juru Tingkat I",
           "II/a": "Pengatur Muda", "II/b": "Pengatur Muda Tingkat I", "II/c": "Pengatur",
           "II/d": "Pengatur Tingkat I", "III/a": "Penata Muda", "III/b": "Penata Muda Tingkat I",
           "III/c": "Penata", "III/d": "Penata Tingkat I", "IV/a": "Pembina",
           "IV/b": "Pembina Tingkat I", "IV/c": "Pembina Utama Muda", "IV/d": "Pembina Utama Madya",
           "IV/e": "Pembina Utama"}
ESELON = ["I.a", "I.b", "II.a", "II.b", "III.a", "III.b", "IV.a", "IV.b", "Non eselon"]
JENIS_JABATAN = ["Struktural", "Fungsional", "Pelaksana"]
# Kolom formulir triwulan (kode, judul). Judul boleh diubah; kode jangan, karena dipakai di data.
KOLOM_TW = [("sasaran", "Sasaran dan Indikator"), ("realisasi", "Realisasi"),
            ("rencana", "Rencana Aksi"), ("pendorong", "Faktor Pendorong"),
            ("penghambat", "Faktor Penghambat"), ("upaya", "Upaya"),
            ("bukti", "Bukti Dukung"), ("ket", "Keterangan")]
ROMAWI = {1: "I", 2: "II", 3: "III", 4: "IV"}
BULAN_TW = {1: "Januari - Maret", 2: "April - Juni", 3: "Juli - September", 4: "Oktober - Desember"}
FILE_LOKAL = os.environ.get("REKAP_DATA_FILE", "data.json")


def fmt(d: date) -> str:
    return f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]} {d.year}"


def data_kosong() -> dict:
    return {
        "bidang": [],   # [{"id","nama"}]
        "pekerja": [],  # [{"id","nama","bidang"(opsional, id bidang)}]
        "kategori": [{"id": "k1", "nama": "Laporan harian"}],
        "libur": {},   # {"2026-10-23": "Keterangan"}
        "isian": {},   # {"2026-10-16": {"<id kategori>": ["<id pekerja>", ...]}}
        "triwulan": {},  # {"2026-T1": {"<id bidang>": ["realisasi", "bukti", ...]}}
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
    for k in [k for k in st.session_state if str(k).startswith(("c_", "pend_"))]:
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


TANPA = "Tanpa bidang"


def nama_lengkap(p: dict) -> str:
    depan = (p.get("gelar_depan") or "").strip()
    belakang = (p.get("gelar_belakang") or "").strip()
    return " ".join(x for x in (depan, p["nama"]) if x) + (f", {belakang}" if belakang else "")


def aktif(p: dict) -> bool:
    return p.get("aktif", True)


def nama_bidang(p: dict) -> str:
    peta = {b["id"]: b["nama"] for b in D["bidang"]}
    return peta.get(p.get("bidang"), TANPA)


def kelompok(pks):
    """Bagi pekerja per bidang. Tanpa bidang yang dibuat: satu kelompok tanpa judul."""
    if not D["bidang"]:
        return [(None, list(pks))]
    hasil = []
    for b in D["bidang"]:
        anggota = [p for p in pks if p.get("bidang") == b["id"]]
        if anggota:
            hasil.append((b["nama"], anggota))
    ids = {b["id"] for b in D["bidang"]}
    lain = [p for p in pks if p.get("bidang") not in ids]
    if lain:
        hasil.append((TANPA, lain))
    return hasil


def judul_bidang(nama, jumlah):
    st.markdown(f'<div class="bidang">{html.escape(nama)} · {jumlah} pekerja</div>',
                unsafe_allow_html=True)


def pilih_pekerja(kunci: str, per_nama: bool = False):
    """Pilihan bidang (dan, kalau per_nama, nama) untuk menyaring pekerja.
    Nama tidak dipilih = semua orang di bidang itu."""
    semua = [p for p in D["pekerja"] if aktif(p)]
    hasil = semua
    if D["bidang"]:
        ada_lain = any(nama_bidang(p) == TANPA for p in semua)
        opsi = (["Semua bidang"] + [b["nama"] for b in D["bidang"]]
                + ([TANPA] if ada_lain else []))
        pilih = st.selectbox("Bidang", opsi, key=kunci)
        if pilih != "Semua bidang":
            hasil = [p for p in semua if nama_bidang(p) == pilih]
    if per_nama:
        dipilih = st.multiselect(
            "Nama (kosongkan untuk menampilkan semua)",
            [p["id"] for p in sorted(hasil, key=lambda x: x["nama"].lower())],
            key=f"{kunci}_nama",
            format_func=lambda i: nama_lengkap(next(p for p in hasil if p["id"] == i)),
            placeholder="Semua orang di bidang ini")
        if dipilih:
            hasil = [p for p in hasil if p["id"] in dipilih]
    return hasil


if "tw_tahun" not in st.session_state:
    st.session_state.tw_tahun = date.today().year
if "tw_tw" not in st.session_state:
    st.session_state.tw_tw = (date.today().month - 1) // 3 + 1

if "tgl_in" not in st.session_state:
    st.session_state.tgl_in = jumat_terakhir(date.today())


def atur(kunci: str, nilai):
    st.session_state[kunci] = nilai


def cb_tw_balik(kunci_tw: str, bid: str, kol: str):
    """Centang/lepas satu kolom triwulan untuk satu pegawai lalu langsung simpan."""
    data = st.session_state.data
    tw = data.setdefault("triwulan", {})
    lama = copy.deepcopy(tw.get(kunci_tw))
    isi = {k: list(v) for k, v in (lama or {}).items()}
    daftar = isi.setdefault(bid, [])
    if kol in daftar:
        daftar.remove(kol)
    else:
        daftar.append(kol)
    isi = {k: v for k, v in isi.items() if v}
    if isi:
        tw[kunci_tw] = isi
    else:
        tw.pop(kunci_tw, None)
    try:
        simpan(data)
        st.session_state.pesan_isian = None
    except Bentrok:
        muat_ke_sesi()
        st.session_state.pesan_isian = ("Data sudah diubah orang lain. Data terbaru sudah "
                                        "dimuat, silakan ketuk ulang.")
    except Exception as e:
        if lama is None:
            tw.pop(kunci_tw, None)
        else:
            tw[kunci_tw] = lama
        st.session_state.pesan_isian = f"Gagal menyimpan: {e}"


def cb_tw_lompat(tahun: int, tw: int, pid: str):
    p = next((x for x in st.session_state.data["pekerja"] if x["id"] == pid), None)
    st.session_state.tw_tahun = tahun
    st.session_state.tw_tw = tw
    if p is not None:
        if st.session_state.data["bidang"]:
            st.session_state.f_bidang_tw = nama_bidang(p)
        st.session_state.f_bidang_tw_nama = [pid]
    st.session_state.halaman = "Isian triwulan"


def cb_geser(arah):
    st.session_state.tgl_in = lompat(st.session_state.tgl_in, arah)


def cb_terakhir():
    st.session_state.tgl_in = jumat_terakhir(date.today())


def cb_pilih():
    st.session_state.tgl_in = jumat_terakhir(st.session_state.tgl_in)


def _sudah(data: dict, tgl: str, kid: str, pid: str) -> bool:
    return pid in data["isian"].get(tgl, {}).get(kid, [])


def _simpan_isian(tgl: str, kid: str, pids: list, nilai: bool):
    """Ubah isian lalu langsung simpan. Kalau gagal, ubahan dikembalikan."""
    data = st.session_state.data
    lama = copy.deepcopy(data["isian"].get(tgl))
    isian = {k: list(v) for k, v in (lama or {}).items()}
    daftar = isian.setdefault(kid, [])
    for pid in pids:
        if nilai and pid not in daftar:
            daftar.append(pid)
        if not nilai and pid in daftar:
            daftar.remove(pid)
    isian = {k: v for k, v in isian.items() if v}
    if isian:
        data["isian"][tgl] = isian
    else:
        data["isian"].pop(tgl, None)
    try:
        simpan(data)
        st.session_state.pesan_isian = None
    except Bentrok:
        muat_ke_sesi()
        st.session_state.pesan_isian = ("Data sudah diubah orang lain. Data terbaru sudah "
                                        "dimuat, silakan ketuk ulang.")
    except Exception as e:  # jaringan, token salah, dan sebagainya
        if lama is None:
            data["isian"].pop(tgl, None)
        else:
            data["isian"][tgl] = lama
        st.session_state.pesan_isian = f"Gagal menyimpan: {e}"


def cb_balik(tgl: str, kid: str, pid: str):
    _simpan_isian(tgl, kid, [pid], not _sudah(st.session_state.data, tgl, kid, pid))


def cb_semua(tgl: str, kid: str, pids: list):
    data = st.session_state.data
    semua = all(_sudah(data, tgl, kid, p) for p in pids)
    _simpan_isian(tgl, kid, pids, not semua)


def cb_lompat(tgl: str, pid: str):
    """Dari chip di Belum mengisi: buka Per tanggal untuk tanggal dan nama itu."""
    p = next((x for x in st.session_state.data["pekerja"] if x["id"] == pid), None)
    if p is None:
        return
    st.session_state.tgl_in = date.fromisoformat(tgl)
    if st.session_state.data["bidang"]:
        st.session_state.f_bidang_tgl = nama_bidang(p)
    st.session_state.f_bidang_tgl_nama = [pid]
    st.session_state.halaman = "Per tanggal"


# ------------------------------------------------------------------- tampilan
if not cfg_github():
    st.warning("Mode uji coba: data disimpan di file lokal dan bisa hilang saat aplikasi "
               "dimulai ulang. Isi pengaturan GitHub (lihat README) agar data permanen.")

UTAMA = ["Per tanggal", "Belum mengisi"]
MASTER = ["Pegawai", "Bidang", "Kategori", "Tanggal dikecualikan", "Cadangan dan pindah data"]
TRIWULAN = ["Isian triwulan", "Rekap triwulan"]
HALAMAN = ["Beranda"] + UTAMA + TRIWULAN + MASTER
if st.session_state.get("halaman") not in HALAMAN:
    st.session_state.halaman = "Beranda"
halaman = st.session_state.halaman
IKON = {"Isian triwulan": "checklist", "Rekap triwulan": "rule", "Beranda": "home", "Per tanggal": "event_note", "Belum mengisi": "pending_actions",
        "Pegawai": "groups", "Bidang": "apartment", "Kategori": "sell",
        "Tanggal dikecualikan": "event_busy", "Cadangan dan pindah data": "backup"}
LOGO = ('<svg width="38" height="38" viewBox="0 0 38 38" xmlns="http://www.w3.org/2000/svg">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#34a874"/><stop offset="1" stop-color="#1f6b49"/></linearGradient></defs>'
        '<rect width="38" height="38" rx="10" fill="url(#g)"/>'
        '<rect x="9" y="21" width="4.5" height="8" rx="1.2" fill="#fff" fill-opacity=".55"/>'
        '<rect x="16.7" y="16" width="4.5" height="13" rx="1.2" fill="#fff" fill-opacity=".8"/>'
        '<path d="M10 13.5l4 4 9-9" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" '
        'stroke-linejoin="round" transform="translate(5 -1)"/></svg>')
with st.sidebar:
    st.markdown(f'<div class="brand">{LOGO}<div><div class="b1">Rekap Isian</div>'
                '<div class="b2">Keterisian laporan WFA</div></div></div>',
                unsafe_allow_html=True)

    def tombol_nav(h):
        st.button(h, key=f"nav_{h}", use_container_width=True, icon=f":material/{IKON[h]}:",
                  type="primary" if h == halaman else "secondary",
                  on_click=atur, args=("halaman", h))

    st.markdown('<div class="grup">UTAMA</div>', unsafe_allow_html=True)
    tombol_nav("Beranda")
    st.markdown('<div class="grup">MENU</div>', unsafe_allow_html=True)
    with st.expander("Aktivitas WFA", icon=":material/assignment:", expanded=halaman in UTAMA):
        for h in UTAMA:
            tombol_nav(h)
    with st.expander("Keterisian Triwulan", icon=":material/fact_check:", expanded=halaman in TRIWULAN):
        for h in TRIWULAN:
            tombol_nav(h)
    with st.expander("Master data", icon=":material/database:", expanded=halaman in MASTER):
        for h in MASTER:
            tombol_nav(h)
    st.markdown('<div class="sp"></div>', unsafe_allow_html=True)
    if st.button("Muat ulang", key="nav_muat", use_container_width=True, icon=":material/refresh:",
                 help="Ambil data terbaru dari penyimpanan"):
        muat_ke_sesi()
        st.rerun()
    if cfg_github():
        st.caption(f"Data: {cfg_github()['repo']}")
st.markdown(f'<div class="eyebrow">{"MASTER" if halaman in MASTER else ("KETERISIAN TRIWULAN" if halaman in TRIWULAN else ("RINGKASAN" if halaman == "Beranda" else "AKTIVITAS WFA"))}</div><div class="judul-hal">{halaman}</div>',
            unsafe_allow_html=True)

def pilih_periode(sufiks: str, dengan_tw: bool):
    """Pilih tahun (dan triwulan). Nilai terakhir diingat lintas halaman."""
    tahun_ini = date.today().year
    tahun_opsi = list(range(min(2026, st.session_state.tw_tahun), max(tahun_ini, st.session_state.tw_tahun) + 2))
    k = st.columns(2 if dengan_tw else 1)
    tahun = k[0].selectbox("Tahun", tahun_opsi, index=tahun_opsi.index(st.session_state.tw_tahun),
                           key=f"w_tahun_{sufiks}")
    st.session_state.tw_tahun = tahun
    if dengan_tw:
        tw = k[1].selectbox("Triwulan", [1, 2, 3, 4], index=st.session_state.tw_tw - 1,
                            key=f"w_tw_{sufiks}",
                            format_func=lambda i: f"Triwulan {ROMAWI[i]} ({BULAN_TW[i]})")
        st.session_state.tw_tw = tw
    return st.session_state.tw_tahun, st.session_state.tw_tw


# -------------------------------------------------------------------- beranda
if halaman == "Beranda":
    if not D["pekerja"] or not D["kategori"]:
        st.info("Belum ada pekerja atau kategori. Tambahkan dulu di menu Master (Pegawai dan Kategori).")
    else:
        with st.container(key="kartu_filter"):
            f1, f2, f3 = st.columns(3)
            b_dari = f1.date_input("Dari", value=AWAL_WFA, key="b_dari", format="DD/MM/YYYY")
            b_sampai = f2.date_input("Sampai", value=date.today(), key="b_sampai", format="DD/MM/YYYY")
            with f3:
                pks_b = pilih_pekerja("f_bidang_ber")
        if b_dari > b_sampai:
            st.error("Tanggal awal harus sebelum tanggal akhir.")
        elif (b_sampai - b_dari).days + 1 > MAKS_HARI:
            st.error("Rentang maksimal 2 tahun (731 hari).")
        else:
            kats_b = D["kategori"]
            jumat = []
            d = b_dari
            while d <= b_sampai:
                if d.weekday() == 4 and d.isoformat() not in D["libur"]:
                    jumat.append(d)
                d += timedelta(days=1)
            if not jumat or not pks_b:
                st.info("Belum ada hari Jumat WFA pada rentang ini, atau tidak ada pekerja yang dipilih.")
            else:
                per_hari = []                       # (tanggal, sudah, total)
                per_bidang, per_kat, per_orang = {}, {}, {}
                for t in jumat:
                    iso = t.isoformat()
                    sudah_h = 0
                    for k in kats_b:
                        for p in pks_b:
                            ya = terisi(iso, k["id"], p["id"])
                            sudah_h += ya
                            for kamus, kunci in ((per_bidang, nama_bidang(p)), (per_kat, k["nama"])):
                                a_, b_ = kamus.get(kunci, (0, 0))
                                kamus[kunci] = (a_ + ya, b_ + 1)
                            if not ya:
                                per_orang[p["id"]] = per_orang.get(p["id"], 0) + 1
                    per_hari.append((t, sudah_h, len(kats_b) * len(pks_b)))
                tot_sudah = sum(x[1] for x in per_hari)
                tot_semua = sum(x[2] for x in per_hari)
                persen = lambda a_, b_: round(100 * a_ / b_, 1) if b_ else 0.0
                pembaruan = per_hari[-1]
                st.markdown(
                    '<div class="statcard"><div class="sc-kiri"><span class="tag">Ringkasan</span>'
                    f'<div class="sc-judul">{persen(tot_sudah, tot_semua)}% terisi</div>'
                    f'<div class="sc-ket">{fmt(jumat[0])} s.d. {fmt(jumat[-1])}</div></div>'
                    f'<div class="sc-stat"><div class="sc-lab">Hari Jumat</div><div class="sc-val">{len(jumat)}</div></div>'
                    f'<div class="sc-stat"><div class="sc-lab">Pekerja</div><div class="sc-val">{len(pks_b)}</div></div>'
                    f'<div class="sc-stat"><div class="sc-lab">Sudah</div><div class="sc-val g">{tot_sudah}</div></div>'
                    f'<div class="sc-stat"><div class="sc-lab">Belum</div><div class="sc-val m">{tot_semua - tot_sudah}</div></div>'
                    f'<div class="sc-stat"><div class="sc-lab">Jumat terakhir</div><div class="sc-val">{persen(pembaruan[1], pembaruan[2])}%</div></div>'
                    '</div>', unsafe_allow_html=True)

                g1, g2 = st.columns([3, 2])
                with g1.container(key="kartu_g1"):
                    st.markdown("**Keterisian per Jumat (%)**")
                    tren = pd.DataFrame(
                        {"Tanggal": [pd.Timestamp(x[0]) for x in per_hari],
                         "Keterisian (%)": [persen(x[1], x[2]) for x in per_hari]})
                    st.line_chart(tren, x="Tanggal", y="Keterisian (%)", color="#2b7a57", height=280)
                with g2.container(key="kartu_g2"):
                    st.markdown("**Keterisian per kategori (%)**")
                    dk = pd.DataFrame({"Kategori": list(per_kat),
                                       "Keterisian (%)": [persen(*v) for v in per_kat.values()]})
                    st.bar_chart(dk, x="Kategori", y="Keterisian (%)", color="#2b7a57", height=280)
                h1, h2 = st.columns(2)
                with h1.container(key="kartu_g3"):
                    st.markdown("**Keterisian per bidang (%)**")
                    db = pd.DataFrame({"Bidang": list(per_bidang),
                                       "Keterisian (%)": [persen(*v) for v in per_bidang.values()]})
                    st.bar_chart(db, x="Bidang", y="Keterisian (%)", horizontal=True,
                                 sort="-Keterisian (%)", color="#2b7a57", height=280)
                with h2.container(key="kartu_g4"):
                    st.markdown("**Paling sering belum mengisi**")
                    nama_p = {p["id"]: nama_lengkap(p) for p in pks_b}
                    top = sorted(per_orang.items(), key=lambda kv: (-kv[1], nama_p[kv[0]].lower()))[:8]
                    if top:
                        dt = pd.DataFrame({"Pegawai": [nama_p[k] for k, _ in top],
                                           "Belum terisi": [v for _, v in top]})
                        st.bar_chart(dt, x="Pegawai", y="Belum terisi", horizontal=True,
                                     sort="-Belum terisi", color="#b42318", height=280)
                    else:
                        st.success("Semua sudah mengisi.")

        # ---- keterisian triwulan
        st.markdown('<div class="bidang">Keterisian triwulan</div>', unsafe_allow_html=True)
        with st.container(key="kartu_filter_tw"):
            t_tahun, t_tw = pilih_periode("ber", True)
        kode_tw = [k for k, _ in KOLOM_TW]
        n_kol = len(kode_tw)

        def isi_pegawai(tahun_, tw_, pid):
            return set(D["triwulan"].get(f"{tahun_}-T{tw_}", {}).get(pid, [])) & set(kode_tw)

        sudah_t = sum(len(isi_pegawai(t_tahun, t_tw, p["id"])) for p in pks_b)
        total_t = len(pks_b) * n_kol
        lengkap_t = sum(len(isi_pegawai(t_tahun, t_tw, p["id"])) == n_kol for p in pks_b)
        pers = lambda a_, b_: round(100 * a_ / b_, 1) if b_ else 0.0
        st.markdown(
            f'<div class="statcard"><div class="sc-kiri"><span class="tag">Triwulan {ROMAWI[t_tw]} {t_tahun}</span>'
            f'<div class="sc-judul">{pers(sudah_t, total_t)}% terisi</div>'
            f'<div class="sc-ket">{BULAN_TW[t_tw]}</div></div>'
            f'<div class="sc-stat"><div class="sc-lab">Pegawai</div><div class="sc-val">{len(pks_b)}</div></div>'
            f'<div class="sc-stat"><div class="sc-lab">Lengkap</div><div class="sc-val g">{lengkap_t}</div></div>'
            f'<div class="sc-stat"><div class="sc-lab">Belum lengkap</div><div class="sc-val m">{len(pks_b) - lengkap_t}</div></div>'
            f'<div class="sc-stat"><div class="sc-lab">Isian belum</div><div class="sc-val">{total_t - sudah_t}</div></div>'
            '</div>', unsafe_allow_html=True)
        if pks_b:
            u1, u2 = st.columns(2)
            with u1.container(key="kartu_g5"):
                st.markdown(f"**Keterisian per kolom, Triwulan {ROMAWI[t_tw]} (%)**")
                dkol = pd.DataFrame({
                    "Kolom": [j for _, j in KOLOM_TW],
                    "Keterisian (%)": [pers(sum(k in isi_pegawai(t_tahun, t_tw, p["id"]) for p in pks_b),
                                            len(pks_b)) for k in kode_tw]})
                st.bar_chart(dkol, x="Kolom", y="Keterisian (%)", horizontal=True, sort=False,
                             color="#2b7a57", height=300)
            with u2.container(key="kartu_g6"):
                st.markdown(f"**Keterisian per triwulan, {t_tahun} (%)**")
                dtw = pd.DataFrame({
                    "Triwulan": [f"Triwulan {ROMAWI[i]}" for i in (1, 2, 3, 4)],
                    "Keterisian (%)": [pers(sum(len(isi_pegawai(t_tahun, i, p["id"])) for p in pks_b),
                                            len(pks_b) * n_kol) for i in (1, 2, 3, 4)]})
                st.bar_chart(dtw, x="Triwulan", y="Keterisian (%)", sort=False, color="#2b7a57", height=300)

# ------------------------------------------------------------ keterisian triwulan
if halaman in TRIWULAN and not D["pekerja"]:
    st.info("Belum ada pegawai. Tambahkan dulu di menu Master data > Pegawai.")

if halaman == "Isian triwulan" and D["pekerja"]:
    with st.container(key="kartu_filter"):
        tahun, tw = pilih_periode("isi", True)
        pks_tw = pilih_pekerja("f_bidang_tw", per_nama=True)
    kunci_tw = f"{tahun}-T{tw}"
    isi_tw = D["triwulan"].get(kunci_tw, {})
    kode_ada = {k for k, _ in KOLOM_TW}
    total = len(pks_tw) * len(KOLOM_TW)
    sudah = sum(len(kode_ada & set(isi_tw.get(p["id"], []))) for p in pks_tw)
    st.markdown(
        '<div class="statcard"><div class="sc-kiri"><span class="tag">Triwulan</span>'
        f'<div class="sc-judul">Triwulan {ROMAWI[tw]} {tahun}</div>'
        f'<div class="sc-ket">{BULAN_TW[tw]} · {sudah} dari {total} isian sudah terisi'
        + (" ✓" if total and sudah == total else "") + '</div></div>'
        f'<div class="sc-stat"><div class="sc-lab">Sudah</div><div class="sc-val g">{sudah}</div></div>'
        f'<div class="sc-stat"><div class="sc-lab">Belum</div><div class="sc-val m">{total - sudah}</div></div>'
        f'<div class="sc-stat"><div class="sc-lab">Pegawai</div><div class="sc-val">{len(pks_tw)}</div></div>'
        '</div>', unsafe_allow_html=True)
    st.progress(sudah / total if total else 0.0)
    if st.session_state.get("pesan_isian"):
        st.error(st.session_state.pesan_isian)
    with st.container(key="kartu_tabel"):
        lebar_tw = [2.6] + [1.5] * len(KOLOM_TW)
        kep = st.columns(lebar_tw, vertical_alignment="center")
        kep[0].markdown('<div class="thead-s" style="justify-content:flex-start;padding-left:.7rem">Pegawai</div>',
                        unsafe_allow_html=True)
        for kol, (_, judul) in zip(kep[1:], KOLOM_TW):
            kol.markdown(f'<div class="thead-s">{html.escape(judul)}</div>', unsafe_allow_html=True)
        for judul_b, anggota in kelompok(pks_tw):
            if judul_b:
                judul_bidang(judul_b, len(anggota))
            anggota = sorted(anggota, key=lambda p: (
                -sum(k not in isi_tw.get(p["id"], []) for k, _ in KOLOM_TW), nama_lengkap(p).lower()))
            for p in anggota:
                st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
                baris = st.columns(lebar_tw, vertical_alignment="center")
                nip = p.get("nip", "")
                baris[0].markdown(
                    f'<div class="peg">{html.escape(nama_lengkap(p))}</div>'
                    + (f'<div class="nip">{html.escape(nip)}</div>' if nip else ""),
                    unsafe_allow_html=True)
                for kol, (kode, _) in zip(baris[1:], KOLOM_TW):
                    ya = kode in isi_tw.get(p["id"], [])
                    kol.button("✓ Sudah" if ya else "Belum",
                               key=f"cell_{'sudah' if ya else 'belum'}_tw_{p['id']}_{kode}",
                               on_click=cb_tw_balik, args=(kunci_tw, p["id"], kode))
        st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
        st.caption("Setiap ketukan langsung tersimpan.")

if halaman == "Rekap triwulan" and D["pekerja"]:
    with st.container(key="kartu_filter"):
        tahun, _ = pilih_periode("rek", False)
        pks_r = pilih_pekerja("f_bidang_twr")
    hari_ini = date.today()
    ada = False
    for tw in (1, 2, 3, 4):
        if date(tahun, 3 * tw - 2, 1) > hari_ini:
            continue                       # triwulan belum dimulai
        ada = True
        isi_tw = D["triwulan"].get(f"{tahun}-T{tw}", {})
        kurang = {p["id"]: [j for k, j in KOLOM_TW if k not in isi_tw.get(p["id"], [])] for p in pks_r}
        belum_p = [p for p in pks_r if kurang[p["id"]]]
        n_kurang = sum(len(v) for v in kurang.values())
        st.markdown(
            f'<div class="bidang">Triwulan {ROMAWI[tw]} {tahun} · {BULAN_TW[tw]} · '
            + ("semua lengkap" if not belum_p else
               f"{len(belum_p)} pegawai belum lengkap ({n_kurang} isian)") + '</div>',
            unsafe_allow_html=True)
        for judul_b, anggota in kelompok(belum_p):
            if judul_b:
                st.caption(judul_b)
            for p in sorted(anggota, key=lambda x: (-len(kurang[x["id"]]), nama_lengkap(x).lower())):
                with st.container(border=True):
                    k1, k2 = st.columns([6, 1], vertical_alignment="center")
                    chips = "".join(f'<span class="chip">{html.escape(j)}</span>' for j in kurang[p["id"]])
                    k1.markdown(f'<div class="nama">{html.escape(nama_lengkap(p))} '
                                f'<span class="jml">· {len(kurang[p["id"]])} belum</span></div>{chips}',
                                unsafe_allow_html=True)
                    k2.button("Buka", key=f"buka_tw_{tahun}_{tw}_{p['id']}", on_click=cb_tw_lompat,
                              args=(tahun, tw, p["id"]), help="Buka di Isian triwulan")
    if not ada:
        st.info("Belum ada triwulan yang dimulai pada tahun ini.")

# --------------------------------------------------------------- per tanggal
if halaman == "Per tanggal":
    if not D["pekerja"] or not D["kategori"]:
        st.info("Belum ada pekerja atau kategori. Tambahkan dulu di menu Master (Pegawai dan Kategori).")
    else:
        with st.container(key="kartu_filter"):
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

            kats = D["kategori"]
            pks = pilih_pekerja("f_bidang_tgl", per_nama=True)
        status = lambda kid, pid: terisi(tgl, kid, pid)  # noqa: E731

        belum = sum(not status(k["id"], p["id"]) for k in kats for p in pks)
        total = len(kats) * len(pks)
        sudah = total - belum
        st.markdown(
            '<div class="statcard"><div class="sc-kiri">'
            '<span class="tag">WFA Jumat</span>'
            + ('<span class="tag tag-m">Dikecualikan</span>' if tgl in D["libur"] else "")
            + f'<div class="sc-judul">{html.escape(fmt(tgl_d))}</div>'
            f'<div class="sc-ket">{sudah} dari {total} isian sudah terisi'
            + (" ✓" if not belum else "") + '</div></div>'
            '<div class="sc-stat"><div class="sc-lab">Sudah</div>'
            f'<div class="sc-val g">{sudah}</div></div>'
            '<div class="sc-stat"><div class="sc-lab">Belum</div>'
            f'<div class="sc-val m">{belum}</div></div>'
            '<div class="sc-stat"><div class="sc-lab">Total</div>'
            f'<div class="sc-val">{total}</div></div>'
            '<div class="sc-stat"><div class="sc-lab">Pekerja</div>'
            f'<div class="sc-val">{len(pks)}</div></div></div>',
            unsafe_allow_html=True)
        st.progress(sudah / total if total else 0.0)
        if st.session_state.get("pesan_isian"):
            st.error(st.session_state.pesan_isian)

        with st.container(key="kartu_tabel"):
            ada_jabatan = any(p.get("jabatan") for p in pks)
            lebar = [4] + ([3] if ada_jabatan else []) + [2.2] * len(kats)
            geser = 2 if ada_jabatan else 1
            kepala = st.columns(lebar)
            kepala[0].markdown("**Pegawai**")
            if ada_jabatan:
                kepala[1].markdown("**Jabatan**")
            for i, k in enumerate(kats):
                kepala[geser + i].markdown(f"**{k['nama']}**")
                kepala[geser + i].button("Tandai semua", key=f"all_{tgl}_{k['id']}", on_click=cb_semua,
                                         args=(tgl, k["id"], [p["id"] for p in pks]))
            for judul, anggota in kelompok(pks):
                if judul:
                    judul_bidang(judul, len(anggota))
                # yang paling banyak belum terisi di atas; sama banyak: urut nama
                anggota = sorted(anggota, key=lambda p: (
                    -sum(not status(k["id"], p["id"]) for k in kats),
                    nama_lengkap(p).lower()))
                for p in anggota:
                    st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
                    baris = st.columns(lebar, vertical_alignment="center")
                    nip = p.get("nip", "")
                    baris[0].markdown(
                        f'<div class="peg">{html.escape(nama_lengkap(p))}</div>'
                        + (f'<div class="nip">{html.escape(nip)}</div>' if nip else ""),
                        unsafe_allow_html=True)
                    if ada_jabatan:
                        baris[1].write(p.get("jabatan", ""))
                    for i, k in enumerate(kats):
                        ya = status(k["id"], p["id"])
                        baris[geser + i].button(
                            "✓ Sudah" if ya else "Belum",
                            key=f"cell_{'sudah' if ya else 'belum'}_{k['id']}_{p['id']}",
                            on_click=cb_balik, args=(tgl, k["id"], p["id"]))
            st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
            st.caption("Setiap ketukan langsung tersimpan.")

# -------------------------------------------------------------------- laporan
if halaman == "Belum mengisi":
    if not D["pekerja"] or not D["kategori"]:
        st.info("Belum ada pekerja atau kategori. Tambahkan dulu di menu Master (Pegawai dan Kategori).")
    else:
        a, b, c = st.columns(3)
        dari = a.date_input("Dari", value=AWAL_WFA, key="dari", format="DD/MM/YYYY")
        sampai = b.date_input("Sampai", value=date.today(), key="sampai", format="DD/MM/YYYY")
        nama_kat = {k["id"]: k["nama"] for k in D["kategori"]}
        pilih_kat = c.selectbox("Kategori", ["Semua kategori"] + list(nama_kat.values()))
        pks_lap = pilih_pekerja("f_bidang_lap")
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
                        for p in pks_lap:
                            if not terisi(t, k["id"], p["id"]):
                                per.setdefault(p["id"], []).append((d, k["nama"], k["id"]))
                                tanggal_hitung.add(t)
                d += timedelta(days=1)

            urut = sorted((p for p in pks_lap if p["id"] in per),
                          key=lambda p: (-len(per[p["id"]]), nama_lengkap(p).lower()))
            if not urut:
                st.success("Tidak ada yang belum mengisi pada rentang ini.")
            else:
                jumlah = sum(len(v) for v in per.values())
                st.metric("Pekerja yang belum mengisi", len(urut),
                          help=f"{jumlah} isian di {len(tanggal_hitung)} tanggal")
                st.caption(f"{jumlah} isian belum terisi di {len(tanggal_hitung)} tanggal.")

                def label(x):
                    return fmt(x[0]) + (f" ({x[1]})" if banyak else "")

                baris_teks = []
                for judul, anggota in kelompok(urut):
                    if judul:
                        judul_bidang(judul, len(anggota))
                        baris_teks.append(f"[{judul}]")
                    for p in anggota:
                        with st.container(border=True):
                            st.markdown(
                                f'<div class="nama">{html.escape(nama_lengkap(p))} '
                                f'<span class="jml">· {len(per[p["id"]])} tanggal</span></div>',
                                unsafe_allow_html=True)
                            with st.container(horizontal=True, gap="small"):
                                for x in per[p["id"]]:
                                    st.button(label(x), key=f"chip_{p['id']}_{x[0].isoformat()}_{x[2]}",
                                              on_click=cb_lompat, args=(x[0].isoformat(), p["id"]),
                                              help="Buka tanggal ini di Per tanggal")
                        baris_teks.append(f"{nama_lengkap(p)} belum mengisi: "
                                          + "; ".join(label(x) for x in per[p["id"]]))
                teks = "\n".join(baris_teks)
                st.caption("Teks untuk disalin (tombol salin ada di pojok kanan atas kotak):")
                st.code(teks, language=None)

# ----------------------------------------------------------------------- kelola
def versi() -> int:
    return st.session_state.get("ver", 0)


def selesai_simpan(pesan: str, **setelah):
    """Simpan ke penyimpanan. Kalau berhasil, atur keadaan halaman lalu muat ulang."""
    if commit(pesan):
        for k, v in setelah.items():
            st.session_state[k] = v
        st.session_state.ver = versi() + 1
        st.rerun()


def cb_urut(kol: str):
    """Ketuk judul kolom: urut naik; ketuk lagi: turun; ketuk lagi: naik."""
    kini = st.session_state.get("pg_urut", ("no", True))
    st.session_state.pg_urut = (kol, not kini[1] if kini[0] == kol else True)


def ada_kembar(nama_nama) -> bool:
    kecil = [n.lower() for n in nama_nama]
    return len(set(kecil)) != len(kecil)


def idx(daftar, nilai) -> int:
    return daftar.index(nilai) if nilai in daftar else 0


def halaman_pegawai():
    by_id = {p["id"]: p for p in D["pekerja"]}
    mode = st.session_state.get("pg_mode")          # None (daftar), "baru", atau id pegawai
    if mode not in (None, "baru") and mode not in by_id:
        mode = None
    with st.container(key="kartu_pegawai"):
        if not mode:
            st.button("Tambah pegawai", type="primary", key="pg_tambah",
                      on_click=atur, args=("pg_mode", "baru"))
            if not D["pekerja"]:
                st.write("Belum ada pegawai.")
            cari = " ".join(st.text_input(
                "Pencarian", key="pg_cari", icon=":material/search:",
                placeholder="Cari nama, NIP, jabatan, atau bidang...",
                label_visibility="collapsed").lower().split())
            hitung = {}
            for x in D["pekerja"]:
                hitung.setdefault(" ".join(x["nama"].lower().split()), []).append(x)
                if x.get("nip"):
                    hitung.setdefault("nip:" + "".join(str(x["nip"]).split()), []).append(x)
            ganda = sorted({nama_lengkap(x) for v in hitung.values() if len(v) > 1 for x in v})
            if ganda:
                st.warning("Ada data yang tampak ganda (nama atau NIP sama): " + ", ".join(ganda)
                           + ". Ubah atau hapus salah satunya.")
            lebar = [1.2, 2.7, 4.2, 3.0, 2.2, 1.7]
            kolom = [("no", "No."), ("nip", "NIP"), ("nama", "Nama Pegawai"),
                     ("jabatan", "Jabatan"), ("bidang", "Bidang")]
            kini, naik = st.session_state.get("pg_urut", ("no", True))
            kepala = st.columns(lebar)
            for kol, (kode, judul) in zip(kepala, kolom):
                tanda = ("▲" if naik else "▼") if kode == kini else "⇅"
                kol.button(f"{judul}  {tanda}", key=f"thead_{kode}", on_click=cb_urut, args=(kode,))
            kepala[5].markdown('<div class="thead">#</div>', unsafe_allow_html=True)
            kunci_urut = {
                "no": lambda x: x["nama"].lower(),
                "nip": lambda x: "".join(str(x.get("nip", "")).split()),
                "nama": lambda x: x["nama"].lower(),
                "jabatan": lambda x: (x.get("jabatan", "") == "", x.get("jabatan", "").lower()),
                "bidang": lambda x: (nama_bidang(x).lower(), x["nama"].lower()),
            }[kini]
            urut = sorted(D["pekerja"], key=kunci_urut, reverse=not naik)
            if cari:
                urut = [x for x in urut if cari in " ".join(
                    [x["nama"], str(x.get("nip", "")), x.get("jabatan", ""), nama_bidang(x)]).lower()]
                if not urut:
                    st.info("Tidak ada pegawai yang cocok dengan pencarian.")
            for no, p in enumerate(urut, 1):
                st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
                k = st.columns(lebar, vertical_alignment="center")
                k[0].write(f"{no}.")
                k[1].write(p.get("nip", ""))
                k[2].markdown(f"{html.escape(nama_lengkap(p))}"
                              + ("" if aktif(p) else " *(nonaktif)*"))
                k[3].write(p.get("jabatan", ""))
                k[4].write(nama_bidang(p) if D["bidang"] else "")
                t1, t2 = k[5].columns(2)
                t1.button("✏️", key=f"pgedit_{p['id']}", help="Ubah",
                          on_click=atur, args=("pg_mode", p["id"]))
                t2.button("🗑️", key=f"pghapus_{p['id']}", help="Hapus",
                          on_click=atur, args=("pg_hapus", p["id"]))
                if st.session_state.get("pg_hapus") == p["id"]:
                    st.warning(f"Hapus {nama_lengkap(p)}? Isian yang tercatat atas nama ini "
                               "ikut hilang dari rekap.")
                    y, n, _ = st.columns([1, 1, 4])
                    if y.button("Ya, hapus", type="primary", key=f"pgya_{p['id']}"):
                        D["pekerja"] = [x for x in D["pekerja"] if x["id"] != p["id"]]
                        selesai_simpan("Dihapus.", pg_hapus=None)
                    n.button("Batal", key=f"pgbatal_{p['id']}", on_click=atur, args=("pg_hapus", None))
            st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
            return

        p = by_id.get(mode, {})
        st.markdown("#### Form Pegawai")
        st.caption("Formulir tambah/ubah data pegawai.")
        pilih_teks = lambda v: "Pilih..." if not v else v
        with st.form(f"form_pg_{mode}_{versi()}"):
            k1, k2 = st.columns([3, 2])
            nip = k1.text_input("NIP Pegawai", value=p.get("nip", ""), placeholder="NIP Pegawai")
            aktif_v = k2.radio("Aktif", ["Ya", "Tidak"], index=0 if aktif(p) else 1, horizontal=True)
            g1, g2, g3 = st.columns([1.3, 4, 1.5])
            gd = g1.text_input("Gelar depan", value=p.get("gelar_depan", ""), placeholder="Gelar depan")
            nama = g2.text_input("Nama pegawai", value=p.get("nama", ""), placeholder="Nama pegawai")
            gb = g3.text_input("Gelar belakang", value=p.get("gelar_belakang", ""),
                               placeholder="Gelar belakang")
            h1, h2, h3, h4 = st.columns([2, 1.4, 1.8, 3])
            gol = h1.selectbox("Golongan", [""] + GOLONGAN, format_func=pilih_teks,
                               index=idx([""] + GOLONGAN, p.get("golongan", "")))
            esl = h2.selectbox("Eselon", [""] + ESELON, format_func=pilih_teks,
                               index=idx([""] + ESELON, p.get("eselon", "")))
            jns = h3.selectbox("Jenis jabatan", [""] + JENIS_JABATAN, format_func=pilih_teks,
                               index=idx([""] + JENIS_JABATAN, p.get("jenis_jabatan", "")))
            jab = h4.text_input("Jabatan pegawai", value=p.get("jabatan", ""),
                                placeholder="Jabatan pegawai")
            bid = ""
            if D["bidang"]:
                peta = {b["id"]: b["nama"] for b in D["bidang"]}
                opsi = [""] + list(peta)
                bid = st.selectbox("Bidang", opsi, index=idx(opsi, p.get("bidang", "")),
                                   format_func=lambda i: TANPA if not i else peta[i])
            yakin = st.checkbox("Ya, hapus pegawai ini") if mode != "baru" else False
            t1, t2, t3, _ = st.columns([1, 1, 1, 3])
            simpan = t1.form_submit_button("Simpan", type="primary")
            kembali = t2.form_submit_button("Kembali")
            hapus = t3.form_submit_button("Hapus") if mode != "baru" else False

            if kembali:
                st.session_state.pg_mode = None
                st.rerun()
            if hapus:
                if not yakin:
                    st.error("Centang dulu \"Ya, hapus pegawai ini\".")
                else:
                    D["pekerja"] = [x for x in D["pekerja"] if x["id"] != mode]
                    selesai_simpan("Dihapus.", pg_mode=None)
            if simpan:
                nama, nip = nama.strip(), "".join(nip.split())
                lain = next((x for x in D["pekerja"]
                             if x["id"] != mode and "".join(str(x.get("nip", "")).split()) == nip), None)
                if not nama:
                    st.error("Nama pegawai wajib diisi.")
                elif not nip:
                    st.error("NIP wajib diisi.")
                elif lain:
                    st.error(f"NIP itu sudah dipakai {nama_lengkap(lain)}.")
                else:
                    baru = dict(p) if mode != "baru" else {"id": uuid.uuid4().hex[:8]}
                    isi = {"nama": nama, "nip": nip, "gelar_depan": gd.strip(),
                           "gelar_belakang": gb.strip(), "golongan": gol, "eselon": esl,
                           "jenis_jabatan": jns, "jabatan": jab.strip(), "bidang": bid}
                    for kunci, v in isi.items():
                        if v or kunci == "nama":
                            baru[kunci] = v
                        else:
                            baru.pop(kunci, None)
                    if aktif_v == "Tidak":
                        baru["aktif"] = False
                    else:
                        baru.pop("aktif", None)
                    if mode != "baru":
                        D["pekerja"] = [baru if x["id"] == mode else x for x in D["pekerja"]]
                    else:
                        D["pekerja"].append(baru)
                    selesai_simpan("Tersimpan.", pg_mode=None)


def daftar_sederhana(judul: str, kunci: str, hint: str):
    """Daftar nama dengan tombol Ubah nama dan Hapus per baris, dan kolom tambah di bawah."""
    k_edit, k_hapus = f"edit_{kunci}", f"hapus_{kunci}"
    with st.expander(f"{judul} ({len(D[kunci])})", expanded=True):
        st.caption(hint)
        if not D[kunci]:
            st.write("Belum ada.")
        for x in D[kunci]:
            c1, c2, c3 = st.columns([5, 1.8, 1.6], vertical_alignment="center")
            if st.session_state.get(k_edit) == x["id"]:
                baru = c1.text_input("Nama", value=x["nama"], key=f"nm_{kunci}_{x['id']}",
                                     label_visibility="collapsed")
                c3.button("Batal", key=f"bt_{kunci}_{x['id']}", on_click=atur, args=(k_edit, None))
                if c2.button("Simpan", key=f"sv_{kunci}_{x['id']}", type="primary"):
                    baru = baru.strip()
                    if not baru:
                        st.error("Nama tidak boleh kosong.")
                    elif ada_kembar([y["nama"] for y in D[kunci] if y["id"] != x["id"]] + [baru]):
                        st.error("Nama itu sudah ada.")
                    else:
                        x["nama"] = baru
                        selesai_simpan("Nama diubah.", **{k_edit: None})
            elif st.session_state.get(k_hapus) == x["id"]:
                c1.write(f"Hapus **{x['nama']}**?")
                c3.button("Batal", key=f"bh_{kunci}_{x['id']}", on_click=atur, args=(k_hapus, None))
                if c2.button("Ya, hapus", key=f"yh_{kunci}_{x['id']}", type="primary"):
                    D[kunci] = [y for y in D[kunci] if y["id"] != x["id"]]
                    selesai_simpan("Dihapus.", **{k_hapus: None})
            else:
                c1.write(x["nama"])
                c2.button("Ubah nama", key=f"ub_{kunci}_{x['id']}", on_click=atur,
                          args=(k_edit, x["id"]))
                c3.button("Hapus", key=f"hp_{kunci}_{x['id']}", on_click=atur,
                          args=(k_hapus, x["id"]))
        with st.form(f"tambah_{kunci}", clear_on_submit=True):
            nama = st.text_input(f"Tambah {judul.lower()}", placeholder="Nama baru")
            if st.form_submit_button("Tambah"):
                nama = nama.strip()
                if not nama:
                    st.error("Nama tidak boleh kosong.")
                elif ada_kembar([y["nama"] for y in D[kunci]] + [nama]):
                    st.error("Nama itu sudah ada.")
                else:
                    D[kunci].append({"id": uuid.uuid4().hex[:8], "nama": nama})
                    selesai_simpan("Ditambahkan.")


def daftar_libur():
    with st.expander(f"Tanggal dikecualikan ({len(D['libur'])})", expanded=True):
        st.caption("Tanggal merah atau hari lain yang tidak perlu diisi. "
                   "Tidak dihitung sebagai belum mengisi.")
        if not D["libur"]:
            st.write("Belum ada.")
        for t in sorted(D["libur"]):
            c1, c2, c3 = st.columns([5, 1.8, 1.6], vertical_alignment="center")
            ket = D["libur"][t]
            if st.session_state.get("hapus_libur") == t:
                c1.write(f"Hapus **{fmt(date.fromisoformat(t))}**?")
                c3.button("Batal", key=f"bh_libur_{t}", on_click=atur, args=("hapus_libur", None))
                if c2.button("Ya, hapus", key=f"yh_libur_{t}", type="primary"):
                    D["libur"].pop(t, None)
                    selesai_simpan("Dihapus.", hapus_libur=None)
            else:
                c1.write(fmt(date.fromisoformat(t)) + (f" · {ket}" if ket else ""))
                c3.button("Hapus", key=f"hp_libur_{t}", on_click=atur, args=("hapus_libur", t))
        with st.form("tambah_libur", clear_on_submit=True):
            l1, l2 = st.columns([2, 3])
            tl = l1.date_input("Tanggal", value=jumat_terakhir(date.today()), format="DD/MM/YYYY")
            kl = l2.text_input("Keterangan (boleh kosong)", placeholder="Contoh: Hari Raya")
            if st.form_submit_button("Tambah"):
                D["libur"][tl.isoformat()] = kl.strip()
                selesai_simpan("Ditambahkan.")


def cadangan():
    with st.expander("Cadangan dan pindah data", expanded=True):
        st.caption("Unduh seluruh data sebagai file, atau muat file data dari tempat lain. "
                   "Memuat file akan **mengganti semua data** yang ada sekarang.")
        st.download_button("Unduh data.json",
                           json.dumps(D, ensure_ascii=False, indent=1, sort_keys=True),
                           file_name="data.json", mime="application/json")
        with st.form("impor"):
            berkas = st.file_uploader("File data.json", type=["json"])
            yakin = st.checkbox("Ya, ganti semua data dengan isi file ini")
            if st.form_submit_button("Muat file"):
                if berkas is None:
                    st.error("Pilih filenya dulu.")
                elif not yakin:
                    st.error("Centang dulu \"Ya, ganti semua data\".")
                else:
                    try:
                        baru = json.load(berkas)
                        assert isinstance(baru, dict)
                        assert isinstance(baru.get("pekerja"), list)
                        assert isinstance(baru.get("kategori"), list)
                        assert isinstance(baru.get("bidang", []), list)
                        assert isinstance(baru.get("libur", {}), dict)
                        assert isinstance(baru.get("isian", {}), dict)
                    except Exception:
                        st.error("File tidak dikenali sebagai data rekap.")
                    else:
                        for kunci, awal in data_kosong().items():
                            baru.setdefault(kunci, awal)
                        st.session_state.data = baru
                        selesai_simpan("Data dimuat.")


if halaman == "Pegawai":
    halaman_pegawai()
if halaman == "Bidang":
    daftar_sederhana("Bidang", "bidang", "Pengelompokan pegawai, misalnya bidang atau seksi. "
                     "Boleh dikosongkan kalau tidak diperlukan. Setelah ditambah, pilih bidang "
                     "di formulir pegawai.")
if halaman == "Kategori":
    daftar_sederhana("Kategori", "kategori", "Jenis isian, misalnya laporan harian.")
    st.caption("Menghapus kategori menyembunyikannya dari rekap. "
               "Riwayat isiannya tetap tersimpan di file data.")
if halaman == "Tanggal dikecualikan":
    daftar_libur()
if halaman == "Cadangan dan pindah data":
    cadangan()
