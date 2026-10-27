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

import requests
import streamlit as st

st.set_page_config(page_title="Rekap Isian Pekerja", page_icon="✅", layout="centered")

st.markdown("""
<style>
.block-container{padding-top:2.2rem;padding-bottom:4rem;max-width:880px}
h1{font-size:1.75rem !important;font-weight:700 !important;letter-spacing:-.01em;padding-bottom:.2rem}
h3{font-size:1.15rem !important}
.stTabs [data-baseweb="tab-list"]{gap:.4rem}
.stTabs [data-baseweb="tab"]{font-weight:600;padding:.6rem .9rem}
[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.28);border-radius:10px;padding:.8rem 1rem;
  background:rgba(128,128,128,.07)}
[data-testid="stForm"]{border-radius:10px;border-color:rgba(128,128,128,.28)}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:10px}
.nama{font-weight:650;font-size:1.02rem;margin-bottom:.35rem}
.jml{font-weight:400;opacity:.65;font-size:.88rem}
.chip{display:inline-block;margin:.15rem .4rem .15rem 0;padding:.12rem .7rem;border-radius:999px;
  background:rgba(217,72,43,.14);color:#d9482b;font-size:.86rem;font-weight:500;white-space:nowrap}
[class*="st-key-chip_"],[class*="st-key-chip_"] [data-testid="stButton"]{width:auto}
[class*="st-key-chip_"] button{min-height:0;padding:.12rem .7rem;border:0 !important;border-radius:999px;
  background:rgba(217,72,43,.14) !important;color:#d9482b !important;font-size:.86rem;font-weight:500}
[class*="st-key-chip_"] button:hover{filter:brightness(.93)}
[data-testid="InputInstructions"]{display:none}
.ket{opacity:.7;font-size:.9rem}
.garis{border-top:1px solid rgba(128,128,128,.3);margin:.3rem 0}
.peg{font-weight:650}
.nip{font-size:.85rem;opacity:.7;font-variant-numeric:tabular-nums}
[class*="st-key-cell_"],[class*="st-key-cell_"] [data-testid="stButton"]{width:100%}
[class*="st-key-cell_"] button{width:100%;border:0 !important;font-weight:600;min-height:2.6rem}
[class*="st-key-cell_belum_"] button{background:rgba(217,72,43,.14) !important;color:#d9482b !important}
[class*="st-key-cell_sudah_"] button{background:rgba(31,138,85,.18) !important;color:#1f8a55 !important}
[class*="st-key-cell_"] button:hover{filter:brightness(.95)}
@media (max-width: 640px){
  [data-testid="stHorizontalBlock"]:has([class*="st-key-cell_"]),
  [data-testid="stHorizontalBlock"]:has([class*="st-key-all_"]){flex-wrap:nowrap !important;gap:.5rem !important}
  [data-testid="stHorizontalBlock"]:has([class*="st-key-cell_"]) > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:has([class*="st-key-all_"]) > [data-testid="stColumn"]{min-width:0 !important}
  [class*="st-key-cell_"] button{font-size:.85rem;padding:.25rem .4rem}
  [class*="st-key-all_"] button{font-size:.75rem;padding:.2rem .4rem}
}
.bidang{font-weight:700;font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;opacity:.8;margin:.9rem 0 .4rem}
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
ESELON = ["I.a", "I.b", "II.a", "II.b", "III.a", "III.b", "IV.a", "IV.b", "Non eselon"]
JENIS_JABATAN = ["Struktural", "Fungsional", "Pelaksana"]
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
            [p["id"] for p in hasil], key=f"{kunci}_nama",
            format_func=lambda i: nama_lengkap(next(p for p in hasil if p["id"] == i)),
            placeholder="Semua orang di bidang ini")
        if dipilih:
            hasil = [p for p in hasil if p["id"] in dipilih]
    return hasil


if "tgl_in" not in st.session_state:
    st.session_state.tgl_in = jumat_terakhir(date.today())


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

HALAMAN = ["Per tanggal", "Belum mengisi", "Kelola"]
if "halaman" not in st.session_state:
    st.session_state.halaman = HALAMAN[0]
halaman = st.segmented_control("Halaman", HALAMAN, key="halaman",
                               label_visibility="collapsed") or HALAMAN[0]

# --------------------------------------------------------------- per tanggal
if halaman == "Per tanggal":
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

        kats = D["kategori"]
        pks = pilih_pekerja("f_bidang_tgl", per_nama=True)
        status = lambda kid, pid: terisi(tgl, kid, pid)  # noqa: E731

        belum = sum(not status(k["id"], p["id"]) for k in kats for p in pks)
        total = len(kats) * len(pks)
        sudah = total - belum
        st.progress(sudah / total if total else 0.0,
                    text=f"{fmt(tgl_d)} · {sudah} dari {total} sudah terisi"
                         + (" ✓" if not belum else ""))
        if st.session_state.get("pesan_isian"):
            st.error(st.session_state.pesan_isian)

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
        st.info("Belum ada pekerja atau kategori. Tambahkan dulu di tab Kelola.")
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


def atur(kunci: str, nilai):
    st.session_state[kunci] = nilai


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
    with st.expander(f"Pegawai ({len(D['pekerja'])})", expanded=True):
        if not mode:
            st.button("Tambah pegawai", type="primary", key="pg_tambah",
                      on_click=atur, args=("pg_mode", "baru"))
            if not D["pekerja"]:
                st.write("Belum ada pegawai.")
            hitung = {}
            for x in D["pekerja"]:
                hitung.setdefault(" ".join(x["nama"].lower().split()), []).append(x)
                if x.get("nip"):
                    hitung.setdefault("nip:" + "".join(str(x["nip"]).split()), []).append(x)
            ganda = sorted({nama_lengkap(x) for v in hitung.values() if len(v) > 1 for x in v})
            if ganda:
                st.warning("Ada data yang tampak ganda (nama atau NIP sama): " + ", ".join(ganda)
                           + ". Ubah atau hapus salah satunya.")
            for p in sorted(D["pekerja"], key=lambda x: x["nama"].lower()):
                c1, c2 = st.columns([6, 1.5], vertical_alignment="center")
                c1.markdown(f"**{nama_lengkap(p)}**")
                info = " · ".join(x for x in (nama_bidang(p) if D["bidang"] else "",
                                              p.get("jabatan", ""),
                                              "" if aktif(p) else "Nonaktif") if x)
                if info:
                    c1.caption(info)
                c2.button("Ubah", key=f"ubah_pg_{p['id']}", on_click=atur, args=("pg_mode", p["id"]))
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
    with st.expander(f"{judul} ({len(D[kunci])})"):
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
    with st.expander(f"Tanggal dikecualikan ({len(D['libur'])})"):
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
    with st.expander("Cadangan dan pindah data"):
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


if halaman == "Kelola":
    halaman_pegawai()
    daftar_sederhana("Bidang", "bidang", "Pengelompokan pegawai, misalnya bidang atau seksi. "
                     "Boleh dikosongkan kalau tidak diperlukan. Setelah ditambah, pilih bidang "
                     "di formulir pegawai.")
    daftar_sederhana("Kategori", "kategori", "Jenis isian, misalnya laporan harian.")
    daftar_libur()
    cadangan()
    st.caption("Menghapus kategori menyembunyikannya dari rekap. "
               "Riwayat isiannya tetap tersimpan di file data.")
