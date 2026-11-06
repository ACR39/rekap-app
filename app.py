"""Rekap Isian Pekerja (versi Streamlit).

Mencatat siapa yang sudah mengisi laporan pada hari Jumat (WFA) dan
menampilkan siapa yang belum. Data disimpan sebagai satu file JSON di
repositori GitHub (disarankan repositori privat terpisah). Kalau pengaturan
GitHub tidak ada, aplikasi memakai file lokal untuk uji coba.
"""
import base64
import copy
import hashlib
import hmac
import html
import json
import os
import re
import time
import uuid
import base64 as _b64
import calendar
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Rekap Isian Pekerja", page_icon="📋", layout="wide")

st.markdown("""
<style>
.block-container{padding:2.6rem 2rem 4rem;max-width:1600px}
[data-testid="stToolbarActions"],[data-testid="stAppDeployButton"],[data-testid="stMainMenu"],
[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none !important}
[data-testid="stHeader"]{background:transparent}
.eyebrow{font-size:.72rem;font-weight:700;letter-spacing:.09em;color:#2b7a57}
.judul-hal{font-size:1.6rem;font-weight:700;color:#111827;margin:.1rem 0 .15rem;letter-spacing:-.01em}
.kepala{display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;
  background:#fff;border:1px solid #e5e7eb;border-left:4px solid #2b7a57;border-radius:12px;
  padding:1rem 1.3rem;margin:0 0 1.4rem;box-shadow:0 1px 3px rgba(15,23,42,.05)}
.kepala .desk{font-size:.86rem;color:#64748b;max-width:62ch}
.pengguna{display:flex;align-items:center;gap:.6rem;background:#f1f5f9;border-radius:999px;padding:.35rem .9rem .35rem .4rem}
.pengguna .av{width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#34a874,#1f6b49);
  color:#fff;font-weight:700;font-size:.85rem;display:flex;align-items:center;justify-content:center}
.pengguna .nm{font-size:.84rem;font-weight:600;color:#0f172a;line-height:1.15}
.pengguna .pr{font-size:.7rem;color:#64748b;text-transform:capitalize}
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
[class*="st-key-chip_cuti_"] button{background:#fff4d6 !important;color:#8a5a00 !important}
[class*="st-key-chip_dl_"] button{background:#e0ecff !important;color:#1d4ed8 !important}
[data-testid="InputInstructions"]{display:none}
.thead-s{background:#256b4a;color:#fff;font-weight:650;font-size:.7rem;letter-spacing:.03em;text-transform:uppercase;text-align:center;padding:.3rem .25rem;border-radius:4px;height:3rem;min-height:3rem;box-sizing:border-box;line-height:1.15;display:flex;align-items:center;justify-content:center}
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
# Keterangan bersifat opsional: tidak dihitung dalam persen, "lengkap", maupun "belum".
KOLOM_WAJIB = [(k, j) for k, j in KOLOM_TW if k != "ket"]

# Data dukung evaluasi SAKIP: (nomor komponen, nama komponen, [(data pendukung, bukti dukung), ...])
SK_KADIS = "SK Kadis (Petunjuk Teknis) Pengelolaan Kinerja Dinas Perhubungan"
DUKUNG = [
    (1, "Perencanaan Kinerja", [
        ("Kebijakan internal/SOP tentang proses penyusunan perencanaan kinerja", SK_KADIS),
        ("RENSTRA", "RENSTRA 2024-2026 dan RENSTRA 2025-2029"),
        ("RKT/RENJA yang telah ditandatangani Kepala PD", "RENJA TA. 2025"),
        ("RKA (Formulir yang menampilkan rekapitulasi program dan kegiatan)", "RKA/DPA TA. 2025"),
        ("Publikasi via Website/Rapat Internal disertai bukti dukung berupa undangan, daftar hadir dan notulen",
         "Bukti Upload di Website, Notulen Rapat/BA RENSTRA/RENJA/RKA/DPA"),
        ("Perjanjian Kinerja dan IKU yang ditandatangani Kepala Perangkat Daerah dengan Gubernur",
         "PK dan IKU TA.2025 Murni dan Perubahan serta PK dan IKU TA.2026"),
        ("Perjanjian Kinerja dan Indikator Kinerja Individu seluruh pegawai yang telah bertanda tangan",
         "PK Eselon III, IV dan IKI Pelaksana & P3K TA.2025 dan TA.2026"),
        ("Realisasi Capaian Kinerja/Pengukuran Kinerja Kepala Dinas dan seluruh pegawai",
         "Laporan Realisasi PK/IKI secara Triwulan TA. 2025"),
        ("Dokumen rencana aksi beserta hasil monev", "Dokumen rencana aksi dan realisasinya"),
        ("Laporan hasil reviu dokumen perencanaan kinerja yang menjelaskan tentang latar belakang dilakukan "
         "revisi (apabila terjadi revisi dokumen perencanaan)", "BA Reviu RENSTRA/RENJA/RKA/DPA/PK/IKI"),
    ]),
    (2, "Pengukuran Kinerja", [
        ("Pergub/SK/SOP internal tentang penyusunan IKI/Pengukuran Kinerja dan Pengumpulan Data Kinerja", SK_KADIS),
        ("SOP pengumpulan data kinerja yang didalamnya mengatur pengumpulan data kinerja secara berkala "
         "dan secara berjenjang", SK_KADIS),
        ("Notulen rapat evaluasi, dokumen pendukung (Laporan Capaian Kinerja, Monev Pembangunan, TEPRA)",
         "Notula/BA Rapat evaluasi Radalok/TEPRA"),
        ("Pengukuran kinerja dan data dukung capaian kinerja (Laporan Kegiatan Triwulan/Semesteran/Tahunan) "
         "yang dilakukan berjenjang", "Laporan Realisasi/Capaian Kinerja PK/IKI secara Triwulan TA. 2025"),
        ("Aplikasi terkait Teknologi Informasi", "e-SAKIP, Website, Google Spreadsheet"),
        ("Reward dan Punishment (Piagam ucapan terimakasih, pengumuman saat rapat (Notulen Rapat), Teguran Lisan)",
         "Piagam, Sertifikat, Surat Teguran, Salinan Pengumuman"),
        ("Mutasi Jabatan didasarkan pada capaian kinerja", "Mutasi, Promosi Jabatan"),
        ("Hasil evaluasi atas pengukuran kinerja",
         "Laporan Evaluasi dari Laporan Realisasi/Capaian Kinerja PK/IKI secara Triwulan TA. 2025"),
        ("Pengajuan formasi analisis jabatan dan analisis beban kerja pada Biro Organisasi dan/atau BKD",
         "Dokumen Anjab/ABK atau revisi Anjab/ABK"),
        ("Cascading dan/atau Croscutting penjabaran sasaran kinerja eselon II",
         "Diagram Cascading dan/atau Croscutting 2025 & 2026 yang bertanda tangan"),
    ]),
    (3, "Pelaporan Kinerja", [
        ("LKjIP (Soft File)", ""),
        ("Lakip telah diupload di Web", ""),
        ("Bukti tanda terima pengiriman Lakip",
         "Bukti Upload di website esr.menpan.go.id dan e-sakip.kaltimprov.go.id"),
    ]),
    (4, "Dokumen Pendukung Lainnya", [
        ("Penghargaan tingkat Provinsi dan Nasional", ""),
        ("Laporan hasil monitoring dan evaluasi capaian kinerja baik capaian PK, IKI, dan Rencana Aksi yang "
         "dilakukan secara berkala (bulanan/triwulan/tahunan) yang menginformasikan kendala/hambatan serta "
         "tindak lanjutnya", ""),
    ]),
]
def struktur_bawaan() -> list:
    """Struktur awal Data dukung evaluasi (dipakai selama belum pernah diedit)."""
    return [{"id": f"s{n}", "nama": nama,
             "baris": [{"id": f"{n}.{i}", "data": d, "bukti": b} for i, (d, b) in enumerate(baris, start=1)]}
            for n, nama, baris in DUKUNG]


def buat_excel_dukung(struktur: list, dk: dict) -> bytes:
    """Tabel Data dukung evaluasi sebagai file Excel (kolom seperti tabel SAKIP)."""
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Data dukung evaluasi"
    tipis = Side(style="thin", color="000000")
    garis = Border(left=tipis, right=tipis, top=tipis, bottom=tipis)
    tengah = Alignment(horizontal="center", vertical="center", wrap_text=True)
    kiri_atas = Alignment(horizontal="left", vertical="top", wrap_text=True)
    kiri_tengah = Alignment(horizontal="left", vertical="center", wrap_text=True)
    judul = ["NO", "KOMPONEN SAKIP", "DATA - DATA PENDUKUNG", "BUKTI DUKUNG", "KETERANGAN", "LINK DATA DUKUNG"]
    for c, (teks, lebar) in enumerate(zip(judul, [6, 24, 62, 42, 24, 42]), start=1):
        sel = ws.cell(row=1, column=c, value=teks)
        sel.font = Font(bold=True)
        sel.alignment = tengah
        sel.border = garis
        ws.column_dimensions[get_column_letter(c)].width = lebar
    ws.row_dimensions[1].height = 22
    ws.freeze_panes = "A2"

    baris_x = 2
    for n, komp in enumerate(struktur, start=1):
        if not komp["baris"]:
            continue
        awal = baris_x
        for i, b in enumerate(komp["baris"], start=1):
            tautan = (dk.get(b["id"], {}).get("link") or "").strip()
            nilai = {3: f"{i}. {b['data']}", 4: b["bukti"] or None,
                     5: dk.get(b["id"], {}).get("ket") or None}
            for c in range(1, 7):
                ws.cell(row=baris_x, column=c).border = garis
            for c, v in nilai.items():
                sel = ws.cell(row=baris_x, column=c, value=v)
                sel.alignment = kiri_tengah if c == 3 else kiri_atas
            sel_l = ws.cell(row=baris_x, column=6)
            if tautan:
                sel_l.value = f"{chr(96 + i) if i <= 26 else i}. {b['data']}"
                if tautan.lower().startswith(("http://", "https://")):
                    sel_l.hyperlink = tautan
                    sel_l.font = Font(color="0563C1", underline="single")
                else:
                    sel_l.value = tautan
            sel_l.alignment = kiri_atas
            baris_x += 1
        akhir = baris_x - 1
        ws.cell(row=awal, column=1, value=n)
        ws.cell(row=awal, column=2, value=komp["nama"].upper())
        for c in (1, 2):
            if akhir > awal:
                ws.merge_cells(start_row=awal, start_column=c, end_row=akhir, end_column=c)
            ws.cell(row=awal, column=c).alignment = Alignment(
                horizontal="center" if c == 1 else "left", vertical="top", wrap_text=True)
        for r in range(awal, akhir + 1):          # garis tepi sel yang digabung
            for c in (1, 2):
                ws.cell(row=r, column=c).border = garis
        for c in range(1, 7):                      # baris pemisah antar komponen
            ws.cell(row=baris_x, column=c).border = garis
        ws.row_dimensions[baris_x].height = 8
        baris_x += 1

    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def get_struktur() -> list:
    return D.get("dukung_struktur") or struktur_bawaan()


ROMAWI = {1: "I", 2: "II", 3: "III", 4: "IV"}
BULAN_TW = {1: "Januari - Maret", 2: "April - Juni", 3: "Juli - September", 4: "Oktober - Desember"}
FILE_LOKAL = os.environ.get("REKAP_DATA_FILE", "data.json")


def grafik_persen(df, kategori, nilai="Keterisian (%)", jenis="bar", horizontal=False,
                  urut=None, tinggi=280):
    """Grafik persen dengan sumbu tetap 0-100%. urut: None = sesuai data, "-y" = terbesar dulu."""
    hijau = "#2b7a57"
    skala = {"domain": [0, 100], "nice": False}
    sumbu_nilai = {"field": nilai, "type": "quantitative", "scale": skala,
                   "axis": {"title": nilai, "values": [0, 25, 50, 75, 100]}}
    if jenis == "line":
        spec = {"mark": {"type": "line", "point": True, "color": hijau},
                "encoding": {"x": {"field": kategori, "type": "temporal",
                                   "axis": {"title": None, "format": "%d/%m/%y"}},
                             "y": sumbu_nilai,
                             "tooltip": [{"field": kategori, "type": "temporal", "format": "%d/%m/%Y"},
                                         {"field": nilai, "type": "quantitative"}]}}
    else:
        urut_k = None if urut is None else urut
        kat = {"field": kategori, "type": "nominal", "sort": urut_k,
               "axis": {"title": None, "labelLimit": 220}}
        if horizontal:
            enc = {"y": kat, "x": sumbu_nilai}
        else:
            kat["axis"]["labelAngle"] = 0
            enc = {"x": kat, "y": sumbu_nilai}
        enc["tooltip"] = [{"field": kategori, "type": "nominal"},
                          {"field": nilai, "type": "quantitative"}]
        spec = {"mark": {"type": "bar", "color": hijau}, "encoding": enc}
    spec["width"] = "container"
    spec["height"] = tinggi
    st.vega_lite_chart(df, spec)


def fmt(d: date) -> str:
    return f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]} {d.year}"


def data_kosong() -> dict:
    return {
        "bidang": [],   # [{"id","nama"}]
        "pekerja": [],  # [{"id","nama","bidang"(opsional, id bidang),"subbidang"(opsional)}]
        "kategori": [{"id": "k1", "nama": "Laporan harian"}],
        "subbidang": [],  # [{"id","nama","bidang"(id bidang induk)}]
        "libur": {},   # {"2026-10-23": "Keterangan"}
        "isian": {},   # {"2026-10-16": {"<id kategori>": ["<id pekerja>", ...]}}
        "triwulan": {},  # {"2026-T1": {"<id pegawai>": ["realisasi", "bukti", ...]}}
        "triwulan_ket": {},  # {"2026-T1": {"<id pegawai>": "teks keterangan"}}
        "absen": {},     # {"2026-10-16": {"<id pegawai>": "Cuti" atau "DL"}}
        "anggaran": [],  # [{"id","tahun","kode","nama","bidang"(id),"pagu","real":{"1":rupiah,...}}]
        "dukung": {},    # {"<id baris>": {"ket": "teks", "link": "https://..."}}  (Data dukung evaluasi)
        "dukung_struktur": [],  # [{"id","nama","baris":[{"id","data","bukti"}]}]; kosong = struktur bawaan
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


def simpan(data: dict, pesan: str = "Perbarui rekap isian"):
    c = cfg_github()
    teks = json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True)
    if c:
        body = {
            "message": pesan,
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
    for k in [k for k in st.session_state if str(k).startswith(("c_", "pend_", "ket_", "abs_", "dk_"))]:
        del st.session_state[k]


def commit(pesan_ok: str | None = None) -> bool:
    """Simpan st.session_state.data. Tampilkan hasilnya ke pengguna."""
    pesan = f"{pesan_ok or 'Perbarui rekap isian'} (oleh {pengguna_nama()})"
    try:
        simpan(st.session_state.data, pesan)
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
# Akun disimpan di Streamlit Secrets, satu bagian per pengguna:
#   [users.budi]
#   nama = "Budi Santoso"
#   peran = "admin"            # "admin" atau "pengisi"
#   password_hash = "pbkdf2$..."   # buat dengan buat_hash.py
# Kalau tidak ada bagian [users], aplikasi memakai kata sandi tunggal lama
# (secret "password") atau, kalau itu juga tidak ada, tanpa login (uji coba).
PERAN = ("admin", "pengisi")
MAKS_GAGAL = 5
KUNCI_DETIK = 60


def _akun() -> dict:
    try:
        u = st.secrets["users"]
        return {str(k): dict(v) for k, v in u.items()}
    except Exception:
        return {}


def cocok_hash(sandi: str, tersimpan: str) -> bool:
    """Cocokkan sandi dengan hash berformat pbkdf2$iterasi$garam_hex$hash_hex."""
    try:
        skema, iterasi, garam, h = str(tersimpan).split("$")
        if skema != "pbkdf2":
            return False
        calon = hashlib.pbkdf2_hmac("sha256", sandi.encode("utf-8"),
                                    bytes.fromhex(garam), int(iterasi))
        return hmac.compare_digest(calon.hex(), h)
    except Exception:
        return False


def pengguna_nama() -> str:
    u = st.session_state.get("user")
    return u["username"] if u else "tamu"


def adalah_admin() -> bool:
    u = st.session_state.get("user")
    return u is None or u.get("peran") == "admin"   # tanpa login = mode uji coba


COOKIE = "rekap_sesi"


def _jam_sesi() -> float:
    try:
        return float(st.secrets.get("sesi_jam", 8))
    except Exception:
        return 8.0


def _kunci_sesi(a: dict) -> bytes:
    """Kunci penanda tangan token. Ikut berubah kalau sandi pengguna diganti, jadi sesi lama batal."""
    try:
        ekstra = str(st.secrets.get("sesi_kunci", ""))
    except Exception:
        ekstra = ""
    return f"{ekstra}|{a.get('password_hash', '')}|{cfg_github() and cfg_github()['token'] or ''}".encode()


def buat_token(uname: str, a: dict) -> str:
    isi = _b64.urlsafe_b64encode(f"{uname}|{int(time.time() + _jam_sesi() * 3600)}".encode()).decode().rstrip("=")
    tanda = hmac.new(_kunci_sesi(a), isi.encode(), hashlib.sha256).hexdigest()
    return f"{isi}.{tanda}"


def baca_token(token: str, akun: dict):
    """Kembalikan username kalau token sah dan belum kedaluwarsa, kalau tidak None."""
    try:
        isi, tanda = token.split(".")
        uname, exp = _b64.urlsafe_b64decode(isi + "=" * (-len(isi) % 4)).decode().split("|")
        a = akun.get(uname)
        if not a or int(exp) < time.time():
            return None
        benar = hmac.new(_kunci_sesi(a), isi.encode(), hashlib.sha256).hexdigest()
        return uname if hmac.compare_digest(benar, tanda) else None
    except Exception:
        return None


def js_cookie(nilai: str, detik: int):
    """Pasang (atau hapus, detik=0) cookie sesi di peramban lewat komponen tak terlihat."""
    import streamlit.components.v1 as components
    components.html(
        f"""<script>
        const d = window.parent.document;
        const aman = window.parent.location.protocol === 'https:' ? '; Secure' : '';
        d.cookie = "{COOKIE}={nilai}; Max-Age={detik}; Path=/; SameSite=Lax" + aman;
        </script>""", height=0)


def keluar():
    for k in ("user", "masuk", "data", "sha"):
        st.session_state.pop(k, None)
    st.session_state.hapus_cookie = True
    st.session_state.cookie_dicek = True


def cek_login():
    akun = _akun()
    if not akun:                       # mode lama / uji coba
        try:
            sandi = st.secrets["password"]
        except Exception:
            return
        if st.session_state.get("masuk"):
            return
        with st.form("login"):
            x = st.text_input("Kata sandi", type="password")
            if st.form_submit_button("Masuk"):
                if hmac.compare_digest(x, str(sandi)):
                    st.session_state.masuk = True
                    st.rerun()
                st.error("Kata sandi salah.")
        st.stop()
    if st.session_state.get("user"):
        return
    if st.session_state.pop("hapus_cookie", False):
        js_cookie("", 0)
    if not st.session_state.get("cookie_dicek"):          # pulihkan sesi setelah refresh
        st.session_state.cookie_dicek = True
        try:
            u = baca_token(st.context.cookies.get(COOKIE, ""), akun)
        except Exception:
            u = None
        if u:
            st.session_state.user = {"username": u, "nama": akun[u].get("nama", u),
                                     "peran": akun[u].get("peran", "pengisi")}
            st.rerun()
    st.markdown("""
<style>
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stToolbar"],
[data-testid="stHeader"]{display:none !important}
[data-testid="stApp"]{background:linear-gradient(160deg,#eef4f0 0%,#f3f4f8 55%,#e6ecf5 100%)}
.block-container{max-width:440px !important;padding:12vh 1.2rem 3rem !important}
.lg-kepala{text-align:center;margin-bottom:1.4rem}
.lg-kepala svg{filter:drop-shadow(0 6px 14px rgba(31,107,73,.28))}
.lg-judul{font-size:1.55rem;font-weight:700;color:#0b1220;margin:.9rem 0 .2rem;letter-spacing:-.01em}
.lg-sub{font-size:.88rem;color:#64748b}
[data-testid="stForm"]{background:#fff;border:1px solid #e2e8f0 !important;border-radius:16px !important;
  padding:1.6rem 1.5rem 1.4rem !important;box-shadow:0 10px 30px rgba(15,23,42,.08)}
[data-testid="stForm"] label p{font-size:.82rem;font-weight:600;color:#334155}
[data-testid="stForm"] input{border-radius:10px}
[data-testid="stForm"] button[kind="secondaryFormSubmit"],[data-testid="stForm"] button[kind="primaryFormSubmit"]{
  background:linear-gradient(135deg,#34a874,#1f6b49) !important;color:#fff !important;border:0 !important;
  border-radius:10px !important;height:2.8rem;font-weight:600;margin-top:.4rem}
[data-testid="stForm"] button[kind="secondaryFormSubmit"]:hover,[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover{
  filter:brightness(1.07)}
[data-testid="stForm"] button:disabled{opacity:.5}
.lg-kaki{text-align:center;font-size:.76rem;color:#94a3b8;margin-top:1.2rem}
</style>
<div class="lg-kepala">
<svg width="56" height="56" viewBox="0 0 38 38" xmlns="http://www.w3.org/2000/svg"><defs>
<linearGradient id="gl" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#34a874"/>
<stop offset="1" stop-color="#1f6b49"/></linearGradient></defs>
<rect width="38" height="38" rx="10" fill="url(#gl)"/>
<rect x="9" y="21" width="4.5" height="8" rx="1.2" fill="#fff" fill-opacity=".55"/>
<rect x="16.7" y="16" width="4.5" height="13" rx="1.2" fill="#fff" fill-opacity=".8"/>
<path d="M10 13.5l4 4 9-9" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round"
stroke-linejoin="round" transform="translate(5 -1)"/></svg>
<div class="lg-judul">Rekap Isian Pekerja</div>
<div class="lg-sub">Masuk untuk melanjutkan</div></div>
""", unsafe_allow_html=True)
    terkunci = st.session_state.get("kunci_sampai", 0) - time.time()
    with st.form("login"):
        uname = st.text_input("Username", placeholder="Masukkan username").strip().lower()
        x = st.text_input("Kata sandi", type="password", placeholder="Masukkan kata sandi")
        kirim = st.form_submit_button("Masuk", use_container_width=True, disabled=terkunci > 0)
    if terkunci > 0:
        st.error(f"Terlalu banyak percobaan. Coba lagi dalam {int(terkunci) + 1} detik.")
    elif kirim:
        a = akun.get(uname)
        # hitung hash walau username tidak ada, supaya waktu responsnya sama
        ok = cocok_hash(x, a["password_hash"] if a and "password_hash" in a
                        else "pbkdf2$1$00$00")
        if a and ok and a.get("peran", "pengisi") in PERAN:
            st.session_state.user = {"username": uname, "nama": a.get("nama", uname),
                                     "peran": a.get("peran", "pengisi")}
            st.session_state.gagal = 0
            st.session_state.pasang_cookie = buat_token(uname, a)
            st.rerun()
        st.session_state.gagal = st.session_state.get("gagal", 0) + 1
        if st.session_state.gagal >= MAKS_GAGAL:
            st.session_state.gagal = 0
            st.session_state.kunci_sampai = time.time() + KUNCI_DETIK
            st.rerun()
        st.error("Username atau kata sandi salah.")
    st.markdown('<div class="lg-kaki">Lupa sandi? Hubungi admin aplikasi.</div>', unsafe_allow_html=True)
    st.stop()


cek_login()
if st.session_state.get("pasang_cookie"):
    js_cookie(st.session_state.pop("pasang_cookie"), int(_jam_sesi() * 3600))

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


STATUS_ABSEN = ["Cuti", "DL"]
STATUS_OPSI = ["Hadir"] + STATUS_ABSEN   # "Hadir" = tidak ada pengecualian


def absen_status(tgl: str, pid: str):
    """Cuti atau DL pada tanggal itu; None kalau tidak ada. Yang ada statusnya tidak dihitung WFA."""
    return D.get("absen", {}).get(tgl, {}).get(pid)


def tw_isi(kunci_tw: str, pid: str) -> set:
    """Kolom wajib triwulan yang sudah terisi untuk satu pegawai. Keterangan opsional, tidak dihitung."""
    kode = {k for k, _ in KOLOM_WAJIB}
    return set(D["triwulan"].get(kunci_tw, {}).get(pid, [])) & kode


TANPA = "Tanpa bidang"


def nama_lengkap(p: dict) -> str:
    depan = (p.get("gelar_depan") or "").strip()
    belakang = (p.get("gelar_belakang") or "").strip()
    return " ".join(x for x in (depan, p["nama"]) if x) + (f", {belakang}" if belakang else "")


def aktif(p: dict) -> bool:
    return p.get("aktif", True)


def ikut_wfa(p: dict) -> bool:
    """Pegawai yang tidak ikut WFA (misalnya beda divisi) tidak dihitung di rekap WFA."""
    return p.get("ikut_wfa", True)


JK_NAMA = {"L": "Laki-laki", "P": "Perempuan"}
STATUS_PEG = ["PNS", "PPPK"]


def status_peg(p: dict) -> str:
    """PNS atau PPPK. Kalau belum diisi, ditebak dari golongan (golongan PPPK -> PPPK); kalau tidak bisa, kosong."""
    st_ = p.get("status_pegawai")
    if st_ in STATUS_PEG:
        return st_
    gol = p.get("golongan", "")
    return "" if not gol else ("PPPK" if gol.startswith("PPPK") else "PNS")


def ke_tgl(v):
    """'2026-03-05' -> date; kosong atau salah format -> None."""
    try:
        return date.fromisoformat(v) if v else None
    except (TypeError, ValueError):
        return None


def ada_pada(p: dict, d: date) -> bool:
    """Pegawai masih bekerja pada tanggal d. Tanpa tanggal masuk dianggap sudah ada;
    tanggal pensiun = hari pertama sudah tidak bekerja."""
    m, k = ke_tgl(p.get("tgl_masuk")), ke_tgl(p.get("tgl_pensiun"))
    return (m is None or m <= d) and (k is None or k > d)


def nama_bidang(p: dict) -> str:
    peta = {b["id"]: b["nama"] for b in D["bidang"]}
    return peta.get(p.get("bidang"), TANPA)


def sub_dari(p: dict):
    """Sub bidang pegawai (dict) kalau valid dan masih di bawah bidangnya, kalau tidak None."""
    sid = p.get("subbidang")
    if not sid:
        return None
    return next((x for x in D["subbidang"]
                 if x["id"] == sid and x["bidang"] == p.get("bidang")), None)


def nama_sub(p: dict) -> str:
    x = sub_dari(p)
    return x["nama"] if x else ""


def nama_unit(p: dict) -> str:
    """Bidang, ditambah sub bidang kalau ada. Dipakai untuk tampilan dan pencarian."""
    n = nama_bidang(p)
    sb = nama_sub(p)
    return f"{n} › {sb}" if sb else n


def kelompok(pks):
    """Bagi pekerja per bidang, lalu per sub bidang di dalamnya.
    Tanpa bidang yang dibuat: satu kelompok tanpa judul."""
    if not D["bidang"]:
        return [(None, list(pks))]
    hasil = []
    for b in D["bidang"]:
        milik = [p for p in pks if p.get("bidang") == b["id"]]
        langsung = [p for p in milik if sub_dari(p) is None]
        if langsung:
            hasil.append((b["nama"], langsung))
        for sb in D["subbidang"]:
            if sb["bidang"] != b["id"]:
                continue
            anggota = [p for p in milik if p.get("subbidang") == sb["id"]]
            if anggota:
                hasil.append((f"{b['nama']} › {sb['nama']}", anggota))
    ids = {b["id"] for b in D["bidang"]}
    lain = [p for p in pks if p.get("bidang") not in ids]
    if lain:
        hasil.append((TANPA, lain))
    return hasil


def judul_bidang(nama, jumlah):
    st.markdown(f'<div class="bidang">{html.escape(nama)} · {jumlah} pekerja</div>',
                unsafe_allow_html=True)


def pilih_pekerja(kunci: str, per_nama: bool = False, wfa: bool = False):
    """Pilihan bidang (dan, kalau per_nama, nama) untuk menyaring pekerja.
    Nama tidak dipilih = semua orang di bidang itu.
    wfa=True: pegawai yang tidak ikut WFA dikeluarkan."""
    semua = [p for p in D["pekerja"] if aktif(p) and (ikut_wfa(p) or not wfa)]
    hasil = semua
    if D["bidang"]:
        ada_lain = any(nama_bidang(p) == TANPA for p in semua)
        opsi = (["Semua bidang"] + [b["nama"] for b in D["bidang"]]
                + ([TANPA] if ada_lain else []))
        pilih = st.selectbox("Bidang", opsi, key=kunci)
        if pilih != "Semua bidang":
            hasil = [p for p in semua if nama_bidang(p) == pilih]
            induk = next((b for b in D["bidang"] if b["nama"] == pilih), None)
            subs = [x for x in D["subbidang"] if induk and x["bidang"] == induk["id"]]
            if subs:
                semua_sub, tanpa_sub = "Semua sub bidang", "Tanpa sub bidang"
                ps = st.selectbox("Sub bidang", [semua_sub] + [x["nama"] for x in subs] + [tanpa_sub],
                                  key=f"{kunci}_sub_{induk['id']}")
                if ps == tanpa_sub:
                    hasil = [p for p in hasil if sub_dari(p) is None]
                elif ps != semua_sub:
                    hasil = [p for p in hasil if nama_sub(p) == ps]
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


def cb_tw_semua(kunci_tw: str, pids: list, kols: list):
    """Tandai semua (atau lepas semua kalau sudah tercentang semua) untuk pegawai dan kolom yang dipilih."""
    data = st.session_state.data
    tw = data.setdefault("triwulan", {})
    lama = copy.deepcopy(tw.get(kunci_tw))
    isi = {k: list(v) for k, v in (lama or {}).items()}
    semua = all(kol in isi.get(pid, []) for pid in pids for kol in kols)
    for pid in pids:
        daftar = isi.setdefault(pid, [])
        for kol in kols:
            if semua and kol in daftar:
                daftar.remove(kol)
            elif not semua and kol not in daftar:
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


def cb_tw_ket(kunci_tw: str, pid: str, kunci_widget: str):
    """Simpan teks keterangan triwulan (diketik manual)."""
    data = st.session_state.data
    kamus = data.setdefault("triwulan_ket", {})
    lama = copy.deepcopy(kamus.get(kunci_tw))
    isi = dict(lama or {})
    teks = " ".join(str(st.session_state.get(kunci_widget, "")).split())
    if teks:
        isi[pid] = teks
    else:
        isi.pop(pid, None)
    if isi:
        kamus[kunci_tw] = isi
    else:
        kamus.pop(kunci_tw, None)
    try:
        simpan(data)
        st.session_state.pesan_isian = None
    except Bentrok:
        muat_ke_sesi()
        st.session_state.pesan_isian = ("Data sudah diubah orang lain. Data terbaru sudah "
                                        "dimuat, silakan ketik ulang.")
    except Exception as e:
        if lama is None:
            kamus.pop(kunci_tw, None)
        else:
            kamus[kunci_tw] = lama
        st.session_state.pesan_isian = f"Gagal menyimpan: {e}"


def ubah_struktur(fn, hapus_id: list | None = None):
    """Ubah struktur Data dukung evaluasi lalu langsung simpan. Gagal/bentrok: dikembalikan."""
    data = st.session_state.data
    lama = copy.deepcopy(data.get("dukung_struktur"))
    lama_dk = copy.deepcopy(data.get("dukung", {}))
    baru = copy.deepcopy(lama) if lama else struktur_bawaan()
    fn(baru)
    data["dukung_struktur"] = baru
    for rid in hapus_id or []:
        data.get("dukung", {}).pop(rid, None)
    try:
        simpan(data)
        st.session_state.pesan_isian = None
    except Bentrok:
        muat_ke_sesi()
        st.session_state.pesan_isian = ("Data sudah diubah orang lain. Data terbaru sudah "
                                        "dimuat, silakan ulangi.")
    except Exception as e:
        data["dukung_struktur"] = lama or []
        data["dukung"] = lama_dk
        st.session_state.pesan_isian = f"Gagal menyimpan: {e}"
    st.session_state.pop("dk_konfirm", None)


def _cari(struktur: list, sid: str):
    return next((k for k in struktur if k["id"] == sid), None)


def _geser(daftar: list, idx: int, arah: int):
    j = idx + arah
    if 0 <= j < len(daftar):
        daftar[idx], daftar[j] = daftar[j], daftar[idx]


def cb_ds_nama(sid: str, kw: str):
    teks = " ".join(str(st.session_state.get(kw, "")).split())
    if not teks:
        st.session_state[kw] = (_cari(get_struktur(), sid) or {}).get("nama", "")
        return
    def fn(st_):
        k = _cari(st_, sid)
        if k:
            k["nama"] = teks
    ubah_struktur(fn)


def cb_ds_baris(sid: str, rid: str, kolom: str, kw: str):
    teks = " ".join(str(st.session_state.get(kw, "")).split())
    if kolom == "data" and not teks:      # data pendukung wajib terisi
        k = _cari(get_struktur(), sid) or {"baris": []}
        st.session_state[kw] = next((b["data"] for b in k["baris"] if b["id"] == rid), "")
        return
    def fn(st_):
        k = _cari(st_, sid)
        b = next((b for b in (k or {"baris": []})["baris"] if b["id"] == rid), None)
        if b:
            b[kolom] = teks
    ubah_struktur(fn)


def cb_ds_tambah_k():
    ubah_struktur(lambda st_: st_.append(
        {"id": "s" + uuid.uuid4().hex[:8], "nama": f"Komponen baru {len(st_) + 1}", "baris": []}))


def cb_ds_geser_k(sid: str, arah: int):
    def fn(st_):
        idx = next((i for i, k in enumerate(st_) if k["id"] == sid), None)
        if idx is not None:
            _geser(st_, idx, arah)
    ubah_struktur(fn)


def cb_ds_hapus_k(sid: str):
    k = _cari(get_struktur(), sid)
    rids = [b["id"] for b in (k or {"baris": []})["baris"]]
    ubah_struktur(lambda st_: st_.__setitem__(slice(None), [x for x in st_ if x["id"] != sid]), rids)


def cb_ds_tambah_b(sid: str):
    def fn(st_):
        k = _cari(st_, sid)
        if k:
            k["baris"].append({"id": "r" + uuid.uuid4().hex[:8], "data": "Data pendukung baru", "bukti": ""})
    ubah_struktur(fn)


def cb_ds_geser_b(sid: str, rid: str, arah: int):
    def fn(st_):
        k = _cari(st_, sid)
        if k:
            idx = next((i for i, b in enumerate(k["baris"]) if b["id"] == rid), None)
            if idx is not None:
                _geser(k["baris"], idx, arah)
    ubah_struktur(fn)


def cb_ds_hapus_b(sid: str, rid: str):
    def fn(st_):
        k = _cari(st_, sid)
        if k:
            k["baris"] = [b for b in k["baris"] if b["id"] != rid]
    ubah_struktur(fn, [rid])


def cb_ds_konfirm(kunci: str):
    st.session_state.dk_konfirm = kunci


def cb_dukung(kid: str, bidang_isi: str, kunci_widget: str):
    """Simpan Keterangan atau Link satu baris Data dukung evaluasi."""
    data = st.session_state.data
    kamus = data.setdefault("dukung", {})
    lama = copy.deepcopy(kamus.get(kid))
    isi = dict(lama or {})
    teks = " ".join(str(st.session_state.get(kunci_widget, "")).split())
    if teks:
        isi[bidang_isi] = teks
    else:
        isi.pop(bidang_isi, None)
    if isi:
        kamus[kid] = isi
    else:
        kamus.pop(kid, None)
    try:
        simpan(data)
        st.session_state.pesan_isian = None
    except Bentrok:
        muat_ke_sesi()
        st.session_state.pesan_isian = ("Data sudah diubah orang lain. Data terbaru sudah "
                                        "dimuat, silakan ketik ulang.")
    except Exception as e:
        if lama is None:
            kamus.pop(kid, None)
        else:
            kamus[kid] = lama
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


def cb_absen(tgl: str, pid: str, kunci_widget: str):
    """Simpan status Cuti/DL satu pegawai pada satu tanggal."""
    data = st.session_state.data
    kamus = data.setdefault("absen", {})
    lama = copy.deepcopy(kamus.get(tgl))
    sebelum = (lama or {}).get(pid, "Hadir")
    isi = dict(lama or {})
    baru = st.session_state.get(kunci_widget, "Hadir")
    if baru in STATUS_ABSEN:
        isi[pid] = baru
    else:
        isi.pop(pid, None)
    if isi:
        kamus[tgl] = isi
    else:
        kamus.pop(tgl, None)
    try:
        simpan(data)
        st.session_state.pesan_isian = None
    except Bentrok:
        muat_ke_sesi()
        st.session_state.pesan_isian = ("Data sudah diubah orang lain. Data terbaru sudah "
                                        "dimuat, silakan ulangi.")
    except Exception as e:
        if lama is None:
            kamus.pop(tgl, None)
        else:
            kamus[tgl] = lama
        st.session_state[kunci_widget] = sebelum
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

UTAMA = ["Per tanggal", "Belum mengisi", "Sudah mengisi", "Rekap cuti dan DL"]
MASTER = ["Pegawai", "Bidang", "Sub bidang", "Tanggal dikecualikan", "Komponen data dukung", "Cadangan dan pindah data"]
TRIWULAN = ["Isian triwulan"]   # menu "Rekap triwulan" disembunyikan dulu
DUKUNG_HAL = "Data dukung evaluasi"
STAT_HAL = "Statistik pegawai"
ANGGARAN_HAL = "Realisasi anggaran"
HALAMAN = ["Beranda"] + UTAMA + TRIWULAN + [STAT_HAL, ANGGARAN_HAL, DUKUNG_HAL] + (MASTER if adalah_admin() else [])
if st.session_state.get("halaman") not in HALAMAN:
    st.session_state.halaman = "Beranda"
halaman = st.session_state.halaman
IKON = {"Realisasi anggaran": "payments", "Statistik pegawai": "bar_chart", "Isian triwulan": "checklist", "Data dukung evaluasi": "folder_open", "Beranda": "home", "Per tanggal": "event_note", "Belum mengisi": "pending_actions", "Sudah mengisi": "task_alt", "Rekap cuti dan DL": "beach_access",
        "Pegawai": "groups", "Bidang": "apartment", "Sub bidang": "account_tree", "Kategori": "sell",
        "Tanggal dikecualikan": "event_busy", "Komponen data dukung": "fact_check", "Cadangan dan pindah data": "backup"}
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
    tombol_nav(STAT_HAL)
    tombol_nav(ANGGARAN_HAL)
    tombol_nav(DUKUNG_HAL)
    if adalah_admin():
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
    if st.session_state.get("user"):
        u = st.session_state.user
        st.markdown('<div class="sp"></div>', unsafe_allow_html=True)
        st.caption(f"Masuk sebagai **{u['nama']}** ({u['peran']})")
        st.button("Keluar", key="nav_keluar", use_container_width=True,
                  icon=":material/logout:", on_click=keluar)
DESKRIPSI = {
    "Beranda": "Ringkasan keterisian laporan WFA dan triwulan.",
    "Per tanggal": "Catat dan lihat isian tiap pegawai pada tanggal tertentu.",
    "Belum mengisi": "Daftar pegawai yang belum melengkapi isian pada rentang tanggal.",
    "Sudah mengisi": "Daftar pegawai yang lengkap mengisi di setiap Jumat dalam rentang tanggal.",
    "Rekap cuti dan DL": "Rekap tanggal cuti dan dinas luar per pegawai.",
    "Isian triwulan": "Tandai kelengkapan isian triwulan tiap pegawai.",
    ANGGARAN_HAL: "Pagu, realisasi, dan serapan anggaran per program, kegiatan, sub kegiatan, dan bidang.",
    STAT_HAL: "Jumlah, penambahan, dan pensiun pegawai per bulan atau triwulan, menurut jenis kelamin.",
    DUKUNG_HAL: "Data pendukung, bukti dukung, dan tautan untuk evaluasi SAKIP.",
    "Pegawai": "Kelola data pegawai, bidang, dan sub bidangnya.",
    "Bidang": "Kelola daftar bidang.",
    "Sub bidang": "Kelola sub bidang di bawah tiap bidang.",
    "Tanggal dikecualikan": "Hari libur atau tanggal yang tidak dihitung dalam rekap.",
    "Komponen data dukung": "Atur komponen dan baris pada tabel data dukung evaluasi.",
    "Cadangan dan pindah data": "Unduh cadangan data atau muat data dari berkas.",
}
_grup = ("MASTER" if halaman in MASTER else ("KETERISIAN TRIWULAN" if halaman in TRIWULAN else
         ("RINGKASAN" if halaman == "Beranda" else ("EVALUASI SAKIP" if halaman == DUKUNG_HAL else ("KEPEGAWAIAN" if halaman == STAT_HAL else ("KEUANGAN" if halaman == ANGGARAN_HAL else "AKTIVITAS WFA"))))))
_u = st.session_state.get("user")
_chip = ""
if _u:
    _chip = (f'<div class="pengguna"><div class="av">{html.escape(_u["nama"][:1].upper())}</div><div>'
             f'<div class="nm">{html.escape(_u["nama"])}</div><div class="pr">{html.escape(_u["peran"])}</div></div></div>')
st.markdown(f'<div class="kepala"><div><div class="eyebrow">{_grup}</div>'
            f'<div class="judul-hal">{html.escape(halaman)}</div>'
            f'<div class="desk">{html.escape(DESKRIPSI.get(halaman, ""))}</div></div>{_chip}</div>',
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


# ---------------------------------------------------------------- statistik pegawai
if halaman == STAT_HAL:
    if not D["pekerja"]:
        st.info("Belum ada pegawai. Tambahkan dulu di menu Master data.")
    else:
        tahun_ini = date.today().year
        tahun_dari = [ke_tgl(p.get("tgl_masuk")).year for p in D["pekerja"] if ke_tgl(p.get("tgl_masuk"))]
        tahun_ke = [ke_tgl(p.get("tgl_pensiun")).year for p in D["pekerja"] if ke_tgl(p.get("tgl_pensiun"))]
        tahun_opsi = list(range(min(tahun_dari + [tahun_ini]), max(tahun_ke + [tahun_ini]) + 1))
        with st.container(key="kartu_filter"):
            f1, f2, f2b, f3 = st.columns([1, 1.4, 1.5, 3])
            th = f1.selectbox("Tahun", tahun_opsi, index=tahun_opsi.index(tahun_ini), key="st_tahun")
            mode = f2.radio("Periode", ["Bulanan", "Triwulanan"], horizontal=True, key="st_mode")
            fs = f2b.radio("Status", ["Semua", "PNS", "PPPK"], horizontal=True, key="st_status")
            with f3:
                pks_st = pilih_pekerja("f_bidang_stat")
        if fs != "Semua":
            pks_st = [p for p in pks_st if status_peg(p) == fs]
        if mode == "Bulanan":
            periode = [(BULAN[m - 1][:3], date(th, m, 1), date(th, m, calendar.monthrange(th, m)[1]))
                       for m in range(1, 13)]
        else:
            periode = [(f"TW {ROMAWI[q]}", date(th, 3 * q - 2, 1),
                        date(th, 3 * q, calendar.monthrange(th, 3 * q)[1])) for q in range(1, 5)]

        def hitung(awal: date, akhir: date):
            sebelum = awal - timedelta(days=1)
            ps = [p for p in pks_st if ada_pada(p, akhir)]
            return {
                "Awal": sum(ada_pada(p, sebelum) for p in pks_st),
                "Masuk": sum(1 for p in pks_st if (ke_tgl(p.get("tgl_masuk")) or date.min) >= awal
                             and ke_tgl(p.get("tgl_masuk")) <= akhir),
                "Pensiun": sum(1 for p in pks_st if ke_tgl(p.get("tgl_pensiun"))
                               and awal <= ke_tgl(p.get("tgl_pensiun")) <= akhir),
                "Akhir": len(ps),
                "Laki-laki": sum(p.get("jk") == "L" for p in ps),
                "Perempuan": sum(p.get("jk") == "P" for p in ps),
                "PNS": sum(status_peg(p) == "PNS" for p in ps),
                "PPPK": sum(status_peg(p) == "PPPK" for p in ps),
                "Belum diisi JK": sum(not p.get("jk") for p in ps),
            }

        baris = [{"Periode": nm, **hitung(a, z)} for nm, a, z in periode]
        df = pd.DataFrame(baris)

        hari_ini = date.today()
        kini = [p for p in pks_st if ada_pada(p, hari_ini)]
        n_pns, n_pppk = sum(status_peg(p) == "PNS" for p in kini), sum(status_peg(p) == "PPPK" for p in kini)
        n_l, n_p = sum(p.get("jk") == "L" for p in kini), sum(p.get("jk") == "P" for p in kini)
        n_masuk, n_pen = int(df["Masuk"].sum()), int(df["Pensiun"].sum())
        st.markdown(
            '<div class="statcard"><div class="sc-kiri">'
            '<span class="tag">Pegawai</span>'
            f'<div class="sc-judul">{len(kini)} pegawai saat ini</div>'
            f'<div class="sc-ket">Per {fmt(hari_ini)}</div></div>'
            f'<div class="sc-stat"><div class="sc-lab">Laki-laki</div><div class="sc-val">{n_l}</div></div>'
            f'<div class="sc-stat"><div class="sc-lab">Perempuan</div><div class="sc-val">{n_p}</div></div>'
            f'<div class="sc-stat"><div class="sc-lab">PNS</div><div class="sc-val">{n_pns}</div></div>'
            f'<div class="sc-stat"><div class="sc-lab">PPPK</div><div class="sc-val">{n_pppk}</div></div>'
            f'<div class="sc-stat"><div class="sc-lab">Masuk {th}</div><div class="sc-val g">{n_masuk}</div></div>'
            f'<div class="sc-stat"><div class="sc-lab">Pensiun {th}</div><div class="sc-val m">{n_pen}</div></div>'
            '</div>', unsafe_allow_html=True)
        lengkap_jk = sum(not p.get("jk") for p in pks_st)
        lengkap_tgl = sum(not p.get("tgl_masuk") for p in pks_st)
        if lengkap_jk or lengkap_tgl:
            st.caption(f"Data belum lengkap: {lengkap_jk} pegawai belum diisi jenis kelamin, "
                       f"{lengkap_tgl} belum diisi tanggal masuk (dianggap sudah bekerja sejak awal). "
                       "Pegawai nonaktif tidak dihitung.")

        urutan = [r["Periode"] for r in baris]
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Jumlah pegawai di akhir periode**")
            panjang = df.melt(id_vars="Periode", value_vars=["Laki-laki", "Perempuan"],
                              var_name="Jenis kelamin", value_name="Jumlah")
            st.vega_lite_chart(panjang, {
                "mark": "bar",
                "encoding": {
                    "x": {"field": "Periode", "type": "nominal", "sort": urutan,
                          "axis": {"title": None, "labelAngle": 0}},
                    "y": {"field": "Jumlah", "type": "quantitative", "axis": {"title": None, "tickMinStep": 1}},
                    "color": {"field": "Jenis kelamin", "type": "nominal",
                              "scale": {"domain": ["Laki-laki", "Perempuan"], "range": ["#2b7a57", "#d98324"]},
                              "legend": {"orient": "bottom", "title": None}},
                    "tooltip": [{"field": "Periode"}, {"field": "Jenis kelamin"}, {"field": "Jumlah"}]},
                "width": "container", "height": 280})
        with g2:
            st.markdown("**Pegawai masuk dan pensiun**")
            panjang2 = df.melt(id_vars="Periode", value_vars=["Masuk", "Pensiun"],
                               var_name="Keterangan", value_name="Jumlah")
            st.vega_lite_chart(panjang2, {
                "mark": "bar",
                "encoding": {
                    "x": {"field": "Periode", "type": "nominal", "sort": urutan,
                          "axis": {"title": None, "labelAngle": 0}},
                    "xOffset": {"field": "Keterangan"},
                    "y": {"field": "Jumlah", "type": "quantitative", "axis": {"title": None, "tickMinStep": 1}},
                    "color": {"field": "Keterangan", "type": "nominal",
                              "scale": {"domain": ["Masuk", "Pensiun"], "range": ["#2b7a57", "#b42318"]},
                              "legend": {"orient": "bottom", "title": None}},
                    "tooltip": [{"field": "Periode"}, {"field": "Keterangan"}, {"field": "Jumlah"}]},
                "width": "container", "height": 280})

        st.markdown("**Tabel rekap**")
        st.dataframe(df, hide_index=True, use_container_width=True, height=(len(df) + 1) * 35 + 3)
        st.download_button("Unduh CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"statistik-pegawai-{th}-{mode.lower()}.csv", mime="text/csv",
                           icon=":material/download:")

        with st.expander("Rincian satu periode", expanded=False):
            idx_p = next((i for i, (_, a, z) in enumerate(periode) if a <= hari_ini <= z), len(periode) - 1)
            pilih = st.selectbox("Periode", range(len(periode)), index=idx_p,
                                 format_func=lambda i: f"{periode[i][0]} {th} ({periode[i][1].strftime('%d/%m/%Y')} - "
                                                       f"{periode[i][2].strftime('%d/%m/%Y')})")
            _, a, z = periode[pilih]
            st.markdown("Per bidang di akhir periode")
            ps = [p for p in pks_st if ada_pada(p, z)]
            ring = []
            for judul, anggota in kelompok(ps):
                ring.append({"Bidang": judul or "Semua pegawai",
                             "Laki-laki": sum(p.get("jk") == "L" for p in anggota),
                             "Perempuan": sum(p.get("jk") == "P" for p in anggota),
                             "PNS": sum(status_peg(p) == "PNS" for p in anggota),
                             "PPPK": sum(status_peg(p) == "PPPK" for p in anggota),
                             "Belum diisi JK": sum(not p.get("jk") for p in anggota),
                             "Total": len(anggota)})
            if ring:
                st.dataframe(pd.DataFrame(ring), hide_index=True, use_container_width=True)
            else:
                st.caption("Tidak ada pegawai pada periode ini.")
            masuk_l = [p for p in pks_st if ke_tgl(p.get("tgl_masuk")) and a <= ke_tgl(p["tgl_masuk"]) <= z]
            pen_l = [p for p in pks_st if ke_tgl(p.get("tgl_pensiun")) and a <= ke_tgl(p["tgl_pensiun"]) <= z]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"Masuk ({len(masuk_l)})")
                for p in sorted(masuk_l, key=lambda x: x["tgl_masuk"]):
                    st.write(f"{nama_lengkap(p)} · {ke_tgl(p['tgl_masuk']).strftime('%d/%m/%Y')}")
                if not masuk_l:
                    st.caption("Tidak ada.")
            with c2:
                st.markdown(f"Pensiun ({len(pen_l)})")
                for p in sorted(pen_l, key=lambda x: x["tgl_pensiun"]):
                    st.write(f"{nama_lengkap(p)} · {ke_tgl(p['tgl_pensiun']).strftime('%d/%m/%Y')}")
                if not pen_l:
                    st.caption("Tidak ada.")

# -------------------------------------------------------------------- beranda
if halaman == "Beranda":
    if not D["pekerja"] or not D["kategori"]:
        st.info("Belum ada pekerja atau kategori. Tambahkan dulu pegawai di menu Master data.")
    else:
        with st.container(key="kartu_filter"):
            f1, f2, f3 = st.columns(3)
            b_dari = f1.date_input("Dari", value=AWAL_WFA, key="b_dari", format="DD/MM/YYYY")
            b_sampai = f2.date_input("Sampai", value=date.today(), key="b_sampai", format="DD/MM/YYYY")
            with f3:
                pks_b_all = pilih_pekerja("f_bidang_ber")
        pks_b = [p for p in pks_b_all if ikut_wfa(p)]   # untuk bagian WFA
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
                            if absen_status(iso, p["id"]):
                                continue          # cuti / DL tidak dihitung
                            ya = terisi(iso, k["id"], p["id"])
                            sudah_h += ya
                            for kamus, kunci in ((per_bidang, nama_bidang(p)), (per_kat, k["nama"])):
                                a_, b_ = kamus.get(kunci, (0, 0))
                                kamus[kunci] = (a_ + ya, b_ + 1)
                            if not ya:
                                per_orang[p["id"]] = per_orang.get(p["id"], 0) + 1
                    n_hitung = sum(not absen_status(iso, p["id"]) for p in pks_b)
                    per_hari.append((t, sudah_h, len(kats_b) * n_hitung))
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

                with st.container(key="kartu_g1"):
                    st.markdown("**Keterisian per Jumat (%)**")
                    tren = pd.DataFrame(
                        {"Tanggal": [pd.Timestamp(x[0]) for x in per_hari],
                         "Keterisian (%)": [persen(x[1], x[2]) for x in per_hari]})
                    grafik_persen(tren, "Tanggal", jenis="line", tinggi=280)
                h1, h2 = st.columns(2)
                with h1.container(key="kartu_g3"):
                    st.markdown("**Keterisian per bidang (%)**")
                    db = pd.DataFrame({"Bidang": list(per_bidang),
                                       "Keterisian (%)": [persen(*v) for v in per_bidang.values()]})
                    grafik_persen(db, "Bidang", horizontal=True, urut="-x", tinggi=280)
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

        # ---- keterisian triwulan (semua pegawai, termasuk yang tidak ikut WFA)
        pks_b = pks_b_all
        st.markdown('<div class="bidang">Keterisian triwulan</div>', unsafe_allow_html=True)
        with st.container(key="kartu_filter_tw"):
            t_tahun, t_tw = pilih_periode("ber", True)
        kode_tw = [k for k, _ in KOLOM_WAJIB]
        n_kol = len(kode_tw)

        def isi_pegawai(tahun_, tw_, pid):
            return tw_isi(f"{tahun_}-T{tw_}", pid)

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
                    "Kolom": [j for _, j in KOLOM_WAJIB],
                    "Keterisian (%)": [pers(sum(k in isi_pegawai(t_tahun, t_tw, p["id"]) for p in pks_b),
                                            len(pks_b)) for k in kode_tw]})
                grafik_persen(dkol, "Kolom", horizontal=True, tinggi=300)
            with u2.container(key="kartu_g6"):
                st.markdown(f"**Keterisian per triwulan, {t_tahun} (%)**")
                dtw = pd.DataFrame({
                    "Triwulan": [f"Triwulan {ROMAWI[i]}" for i in (1, 2, 3, 4)],
                    "Keterisian (%)": [pers(sum(len(isi_pegawai(t_tahun, i, p["id"])) for p in pks_b),
                                            len(pks_b) * n_kol) for i in (1, 2, 3, 4)]})
                grafik_persen(dtw, "Triwulan", tinggi=300)

# ------------------------------------------------------------ keterisian triwulan
if halaman in TRIWULAN and not D["pekerja"]:
    st.info("Belum ada pegawai. Tambahkan dulu di menu Master data > Pegawai.")

if halaman == "Isian triwulan" and D["pekerja"]:
    with st.container(key="kartu_filter"):
        tahun, tw = pilih_periode("isi", True)
        pks_tw = pilih_pekerja("f_bidang_tw", per_nama=True)
        tampil_semua = st.toggle("Tampilkan tombol Tandai semua", value=True, key="tw_tampil_semua",
                                 help="Matikan untuk menyembunyikan tombol agar tidak terketuk tanpa sengaja.")
    kunci_tw = f"{tahun}-T{tw}"
    isi_tw = D["triwulan"].get(kunci_tw, {})
    total = len(pks_tw) * len(KOLOM_WAJIB)
    sudah = sum(len(tw_isi(kunci_tw, p["id"])) for p in pks_tw)
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
        lebar_tw = [2.6] + [1.5] * (len(KOLOM_TW) - 1) + [3.2]
        kep = st.columns(lebar_tw, vertical_alignment="top")
        kep[0].markdown('<div class="thead-s" style="justify-content:flex-start;padding-left:.7rem">Pegawai</div>',
                        unsafe_allow_html=True)
        for kol, (kd, judul) in zip(kep[1:], KOLOM_TW):
            if kd == "ket":
                judul += " (opsional)"
            kol.markdown(f'<div class="thead-s">{html.escape(judul)}</div>', unsafe_allow_html=True)
            if tampil_semua and kd != "ket":
                kol.button("Semua", key=f"all_tw_{kd}", on_click=cb_tw_semua, use_container_width=True,
                           args=(kunci_tw, [p["id"] for p in pks_tw], [kd]),
                           help="Tandai semua: kolom ini untuk semua pegawai yang tampil (ketuk lagi untuk melepas)")
        for judul_b, anggota in kelompok(pks_tw):
            if judul_b:
                judul_bidang(judul_b, len(anggota))
            anggota = sorted(anggota, key=lambda p: (
                -sum(k not in tw_isi(kunci_tw, p["id"]) for k, _ in KOLOM_WAJIB), nama_lengkap(p).lower()))
            for p in anggota:
                st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
                baris = st.columns(lebar_tw, vertical_alignment="center")
                nip = p.get("nip", "")
                baris[0].markdown(
                    f'<div class="peg">{html.escape(nama_lengkap(p))}</div>'
                    + (f'<div class="nip">{html.escape(nip)}</div>' if nip else ""),
                    unsafe_allow_html=True)
                if tampil_semua:
                    baris[0].button("Tandai semua", key=f"all_tw_p_{p['id']}", on_click=cb_tw_semua,
                                    args=(kunci_tw, [p["id"]], [k for k, _ in KOLOM_WAJIB]),
                                    help="Tandai semua kolom pegawai ini (ketuk lagi untuk melepas)")
                for kol, (kode, _) in zip(baris[1:], KOLOM_TW):
                    if kode == "ket":
                        kw = f"ket_{kunci_tw}_{p['id']}"
                        kol.text_input("Keterangan", key=kw, label_visibility="collapsed",
                                       value=D["triwulan_ket"].get(kunci_tw, {}).get(p["id"], ""),
                                       placeholder="Opsional, boleh dikosongkan...", on_change=cb_tw_ket,
                                       args=(kunci_tw, p["id"], kw))
                        continue
                    ya = kode in isi_tw.get(p["id"], [])
                    kol.button("✓ Sudah" if ya else "Belum",
                               key=f"cell_{'sudah' if ya else 'belum'}_tw_{p['id']}_{kode}",
                               on_click=cb_tw_balik, args=(kunci_tw, p["id"], kode))
        st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
        st.caption("Setiap ketukan langsung tersimpan. Keterangan bersifat opsional (tidak dihitung): diketik lalu tekan Enter.")

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
        kurang = {p["id"]: [j for k, j in KOLOM_WAJIB if k not in tw_isi(f"{tahun}-T{tw}", p["id"])]
                  for p in pks_r}
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
        st.info("Belum ada pekerja atau kategori. Tambahkan dulu pegawai di menu Master data.")
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
            pks = pilih_pekerja("f_bidang_tgl", per_nama=True, wfa=True)
            tampil_semua_tgl = st.toggle("Tampilkan tombol Tandai semua", value=False,
                                         key="tgl_tampil_semua",
                                         help="Bawaannya disembunyikan agar tidak terketuk tanpa sengaja.")
        status = lambda kid, pid: terisi(tgl, kid, pid)  # noqa: E731

        pks_hitung = [p for p in pks if not absen_status(tgl, p["id"])]
        n_absen = len(pks) - len(pks_hitung)
        belum = sum(not status(k["id"], p["id"]) for k in kats for p in pks_hitung)
        total = len(kats) * len(pks_hitung)
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
            f'<div class="sc-val">{len(pks_hitung)}</div></div>'
            '<div class="sc-stat"><div class="sc-lab">Cuti/DL</div>'
            f'<div class="sc-val">{n_absen}</div></div></div>',
            unsafe_allow_html=True)
        st.progress(sudah / total if total else 0.0)
        if st.session_state.get("pesan_isian"):
            st.error(st.session_state.pesan_isian)

        with st.container(key="kartu_tabel"):
            ada_jabatan = any(p.get("jabatan") for p in pks)
            lebar = [4] + ([3] if ada_jabatan else []) + [1.7] + [2.2] * len(kats)
            geser = 3 if ada_jabatan else 2
            kepala = st.columns(lebar, vertical_alignment="top")
            kiri = 'style="justify-content:flex-start;padding-left:.7rem"'
            kepala[0].markdown(f'<div class="thead-s" {kiri}>Pegawai</div>', unsafe_allow_html=True)
            if ada_jabatan:
                kepala[1].markdown(f'<div class="thead-s" {kiri}>Jabatan</div>', unsafe_allow_html=True)
            kepala[geser - 1].markdown('<div class="thead-s">Status</div>', unsafe_allow_html=True)
            for i, k in enumerate(kats):
                kepala[geser + i].markdown(f'<div class="thead-s">{html.escape(k["nama"])}</div>',
                                           unsafe_allow_html=True)
                if tampil_semua_tgl:
                    kepala[geser + i].button("Tandai semua", key=f"all_{tgl}_{k['id']}", on_click=cb_semua,
                                             args=(tgl, k["id"], [p["id"] for p in pks_hitung]))
            for judul, anggota in kelompok(pks):
                if judul:
                    judul_bidang(judul, len(anggota))
                # yang paling banyak belum terisi di atas; sama banyak: urut nama
                anggota = sorted(anggota, key=lambda p: (
                    bool(absen_status(tgl, p["id"])),
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
                    sa = absen_status(tgl, p["id"]) or "Hadir"
                    kw_abs = f"abs_{tgl}_{p['id']}"
                    baris[geser - 1].selectbox(
                        "Status", STATUS_OPSI, index=STATUS_OPSI.index(sa), key=kw_abs,
                        label_visibility="collapsed", on_change=cb_absen,
                        args=(tgl, p["id"], kw_abs))
                    for i, k in enumerate(kats):
                        if sa != "Hadir":
                            baris[geser + i].markdown(
                                f'<span class="tag tag-m">{html.escape(sa)}</span>',
                                unsafe_allow_html=True)
                            continue
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
        st.info("Belum ada pekerja atau kategori. Tambahkan dulu pegawai di menu Master data.")
    else:
        with st.container(key="kartu_filter"):
            a, b, c = st.columns(3)
            dari = a.date_input("Dari", value=AWAL_WFA, key="dari", format="DD/MM/YYYY")
            sampai = b.date_input("Sampai", value=date.today(), key="sampai", format="DD/MM/YYYY")
            nama_kat = {k["id"]: k["nama"] for k in D["kategori"]}
            pilih_kat = c.selectbox("Kategori", ["Semua kategori"] + list(nama_kat.values()))
            pks_lap = pilih_pekerja("f_bidang_lap", per_nama=True, wfa=True)
            st.caption("Hanya menghitung hari Jumat. Tanggal yang dikecualikan, serta pegawai yang "
                       "Cuti atau DL pada tanggal itu, dilewati.")

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
                            if absen_status(t, p["id"]):
                                continue          # cuti / DL tidak dihitung
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

                for judul, anggota in kelompok(urut):
                    if judul:
                        judul_bidang(judul, len(anggota))
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

# ------------------------------------------------------------- sudah mengisi
if halaman == "Sudah mengisi":
    if not D["pekerja"] or not D["kategori"]:
        st.info("Belum ada pekerja atau kategori. Tambahkan dulu pegawai di menu Master data.")
    else:
        if "dari_sdh" not in st.session_state:
            st.session_state.dari_sdh = jumat_terakhir(date.today())
        if "sampai_sdh" not in st.session_state:
            st.session_state.sampai_sdh = jumat_terakhir(date.today())
        with st.container(key="kartu_filter"):
            c1, c2, c3 = st.columns([3, 3, 2], vertical_alignment="bottom")
            dari_s = c1.date_input("Dari", key="dari_sdh", format="DD/MM/YYYY")
            sampai_s = c2.date_input("Sampai", key="sampai_sdh", format="DD/MM/YYYY")
            c3.button("Jumat terakhir", key="last_sdh", use_container_width=True,
                      on_click=lambda: st.session_state.update(
                          dari_sdh=jumat_terakhir(date.today()),
                          sampai_sdh=jumat_terakhir(date.today())))
            pks_s = pilih_pekerja("f_bidang_sdh", wfa=True)
            st.caption("Hanya menghitung hari Jumat. Yang tampil adalah pegawai yang lengkap mengisi "
                       "(semua kategori) di setiap Jumat pada rentang ini. Tanggal yang dikecualikan, "
                       "serta Jumat saat pegawai Cuti atau DL, dilewati. Pilih tanggal yang sama di "
                       "Dari dan Sampai untuk satu hari saja.")

        if dari_s > sampai_s:
            st.error("Tanggal awal harus sebelum tanggal akhir.")
        elif (sampai_s - dari_s).days + 1 > MAKS_HARI:
            st.error("Rentang maksimal 2 tahun (731 hari).")
        else:
            jumat_s = []
            d = dari_s
            while d <= sampai_s:
                if d.weekday() == 4 and d.isoformat() not in D["libur"]:
                    jumat_s.append(d.isoformat())
                d += timedelta(days=1)
            if not jumat_s:
                st.info("Tidak ada hari Jumat WFA pada rentang ini.")
            else:
                lengkap = []
                for p in pks_s:
                    hitung = [t for t in jumat_s if not absen_status(t, p["id"])]
                    if hitung and all(terisi(t, k["id"], p["id"])
                                      for t in hitung for k in D["kategori"]):
                        lengkap.append(p)
                st.markdown(
                    '<div class="statcard"><div class="sc-kiri">'
                    '<span class="tag">WFA Jumat</span>'
                    f'<div class="sc-judul">{html.escape(fmt(dari_s))}'
                    + (f' s.d. {html.escape(fmt(sampai_s))}' if dari_s != sampai_s else "")
                    + '</div>'
                    f'<div class="sc-ket">{len(lengkap)} dari {len(pks_s)} pegawai lengkap mengisi '
                    f'· {len(jumat_s)} hari Jumat</div></div>'
                    '<div class="sc-stat"><div class="sc-lab">Sudah lengkap</div>'
                    f'<div class="sc-val g">{len(lengkap)}</div></div>'
                    '<div class="sc-stat"><div class="sc-lab">Belum lengkap</div>'
                    f'<div class="sc-val m">{len(pks_s) - len(lengkap)}</div></div></div>',
                    unsafe_allow_html=True)
                st.progress(len(lengkap) / len(pks_s) if pks_s else 0.0)

                if not lengkap:
                    st.info("Belum ada pegawai yang lengkap mengisi pada rentang ini.")
                else:
                    with st.container(key="kartu_tabel"):
                        for judul, anggota in kelompok(lengkap):
                            if judul:
                                judul_bidang(judul, len(anggota))
                            for p in sorted(anggota, key=lambda p: nama_lengkap(p).lower()):
                                st.markdown(f'<div class="peg">{html.escape(nama_lengkap(p))}</div>',
                                            unsafe_allow_html=True)

# ------------------------------------------------------------ data dukung evaluasi
if halaman == DUKUNG_HAL:
    dk = D.get("dukung", {})
    struktur = get_struktur()
    semua_id = [b["id"] for k in struktur for b in k["baris"]]
    ada_link = sum(bool(dk.get(k, {}).get("link")) for k in semua_id)
    st.markdown(
        '<div class="statcard"><div class="sc-kiri"><span class="tag">SAKIP</span>'
        '<div class="sc-judul">Data dukung evaluasi</div>'
        f'<div class="sc-ket">{ada_link} dari {len(semua_id)} data dukung sudah ada link-nya</div></div>'
        '<div class="sc-stat"><div class="sc-lab">Sudah ada link</div>'
        f'<div class="sc-val g">{ada_link}</div></div>'
        '<div class="sc-stat"><div class="sc-lab">Belum</div>'
        f'<div class="sc-val m">{len(semua_id) - ada_link}</div></div></div>',
        unsafe_allow_html=True)
    st.progress(ada_link / len(semua_id) if semua_id else 0.0)
    try:
        st.download_button("Unduh Excel", data=buat_excel_dukung(struktur, dk), icon=":material/download:",
                           file_name=f"Data dukung evaluasi {date.today().isoformat()}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="unduh_dukung", disabled=not semua_id)
    except ImportError:
        st.warning("Tombol unduh Excel butuh paket openpyxl. Tambahkan baris `openpyxl` di requirements.txt.")
    if st.session_state.get("pesan_isian"):
        st.error(st.session_state.pesan_isian)

    with st.container(key="kartu_tabel"):
        lebar_dk = [0.5, 2, 4.2, 3.2, 2.6, 3]
        kep = st.columns(lebar_dk, vertical_alignment="top")
        for kol, judul in zip(kep, ["No", "Komponen SAKIP", "Data - data pendukung", "Bukti dukung",
                                    "Keterangan", "Link data dukung"]):
            kol.markdown(f'<div class="thead-s">{html.escape(judul)}</div>', unsafe_allow_html=True)
        if not semua_id:
            st.info("Belum ada data dukung. Tambahkan di Master data > Komponen data dukung.")
        for n_komp, komp in enumerate(struktur, start=1):
            nama_komp, baris_dk = komp["nama"], [(b["id"], b["data"], b["bukti"]) for b in komp["baris"]]
            if not baris_dk:
                continue
            st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
            for i, (kid, data_p, bukti) in enumerate(baris_dk, start=1):
                b = st.columns(lebar_dk, vertical_alignment="center")
                if i == 1:
                    b[0].markdown(f"**{n_komp}**")
                    b[1].markdown(f"**{html.escape(nama_komp.upper())}**")
                b[2].markdown(f"{i}. {html.escape(data_p)}")
                b[3].markdown(html.escape(bukti) if bukti else "")
                kw_k, kw_l = f"dk_ket_{kid}", f"dk_link_{kid}"
                b[4].text_input("Keterangan", key=kw_k, label_visibility="collapsed",
                                value=dk.get(kid, {}).get("ket", ""), placeholder="Keterangan...",
                                on_change=cb_dukung, args=(kid, "ket", kw_k))
                tautan = dk.get(kid, {}).get("link", "")
                b[5].text_input("Link", key=kw_l, label_visibility="collapsed", value=tautan,
                                placeholder="Tempel link (Google Drive dll.)...",
                                on_change=cb_dukung, args=(kid, "link", kw_l))
                if tautan.lower().startswith(("http://", "https://")):
                    b[5].markdown(f'<a href="{html.escape(tautan, quote=True)}" target="_blank" '
                                  'rel="noopener noreferrer">Buka tautan ↗</a>', unsafe_allow_html=True)
                st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
        st.caption("Keterangan dan link diketik lalu tekan Enter; setiap isian langsung tersimpan.")

# ------------------------------------------------------------- rekap cuti dan DL
if halaman == "Rekap cuti dan DL":
    if not D["pekerja"]:
        st.info("Belum ada pegawai. Tambahkan dulu di menu Master data > Pegawai.")
    else:
        with st.container(key="kartu_filter"):
            a, b, c = st.columns(3)
            dari_c = a.date_input("Dari", value=AWAL_WFA, key="dari_cd", format="DD/MM/YYYY")
            sampai_c = b.date_input("Sampai", value=date(date.today().year, 12, 31), key="sampai_cd",
                                    format="DD/MM/YYYY")
            jenis_c = c.selectbox("Status", ["Cuti dan DL"] + STATUS_ABSEN, key="jenis_cd")
            pks_c = pilih_pekerja("f_bidang_cd")
        if dari_c > sampai_c:
            st.error("Tanggal awal harus sebelum tanggal akhir.")
        elif (sampai_c - dari_c).days + 1 > MAKS_HARI:
            st.error("Rentang maksimal 2 tahun (731 hari).")
        else:
            boleh = {p["id"] for p in pks_c}
            per_c = {}      # id pegawai -> [(tanggal, status)]
            for t_iso, isi_a in D.get("absen", {}).items():
                try:
                    t_d = date.fromisoformat(t_iso)
                except ValueError:
                    continue
                if not (dari_c <= t_d <= sampai_c):
                    continue
                for pid_, st_ in isi_a.items():
                    if pid_ in boleh and (jenis_c == "Cuti dan DL" or st_ == jenis_c):
                        per_c.setdefault(pid_, []).append((t_d, st_))
            urut_c = sorted((p for p in pks_c if p["id"] in per_c),
                            key=lambda p: (-len(per_c[p["id"]]), nama_lengkap(p).lower()))
            if not urut_c:
                st.success("Tidak ada catatan cuti atau DL pada rentang ini.")
            else:
                n_cuti = sum(s_ == "Cuti" for v in per_c.values() for _, s_ in v)
                n_dl = sum(s_ == "DL" for v in per_c.values() for _, s_ in v)
                m1, m2, m3 = st.columns(3)
                m1.metric("Pegawai", len(urut_c))
                m2.metric("Hari cuti", n_cuti)
                m3.metric("Hari DL", n_dl)
                for judul, anggota in kelompok(urut_c):
                    if judul:
                        judul_bidang(judul, len(anggota))
                    for p in anggota:
                        catatan = sorted(per_c[p["id"]])
                        nc = sum(s_ == "Cuti" for _, s_ in catatan)
                        nd = len(catatan) - nc
                        ringkas = ", ".join(x for x in (f"Cuti {nc}" if nc else "",
                                                        f"DL {nd}" if nd else "") if x)
                        with st.container(border=True):
                            st.markdown(f'<div class="nama">{html.escape(nama_lengkap(p))} '
                                        f'<span class="jml">· {ringkas}</span></div>',
                                        unsafe_allow_html=True)
                            with st.container(horizontal=True, gap="small"):
                                for t_, s_ in catatan:
                                    st.button(f"{fmt(t_)} · {s_}",
                                              key=f"chip_{s_.lower()}_{p['id']}_{t_.isoformat()}",
                                              on_click=cb_lompat, args=(t_.isoformat(), p["id"]),
                                              help="Buka tanggal ini di Per tanggal")

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


# ------------------------------------------------------------ impor pegawai dari Excel
KOLOM_IMPOR = [("nip", "NIP"), ("gelar_depan", "Gelar depan"), ("nama", "Nama"),
               ("gelar_belakang", "Gelar belakang"), ("golongan", "Golongan"), ("eselon", "Eselon"),
               ("jenis_jabatan", "Jenis jabatan"), ("jabatan", "Jabatan"), ("bidang", "Bidang"),
               ("subbidang", "Sub bidang"), ("jk", "Jenis kelamin"), ("tgl_masuk", "Tanggal masuk"),
               ("tgl_pensiun", "Tanggal pensiun"), ("aktif", "Aktif"), ("ikut_wfa", "Ikut WFA"),
               ("status_pegawai", "Status pegawai")]
ALIAS_IMPOR = {
    "nip": {"nip", "nomorindukpegawai"}, "gelar_depan": {"gelardepan"},
    "nama": {"nama", "namapegawai", "namalengkap"}, "gelar_belakang": {"gelarbelakang"},
    "golongan": {"golongan", "gol", "pangkatgolongan"}, "eselon": {"eselon"},
    "jenis_jabatan": {"jenisjabatan"}, "jabatan": {"jabatan", "namajabatan"},
    "bidang": {"bidang", "unitkerja"}, "subbidang": {"subbidang", "subbagian", "seksi"},
    "jk": {"jeniskelamin", "jk", "kelamin", "gender"},
    "tgl_masuk": {"tanggalmasuk", "tglmasuk", "tmtmasuk"},
    "tgl_pensiun": {"tanggalpensiun", "tglpensiun", "tmtpensiun"},
    "aktif": {"aktif", "statusaktif"}, "ikut_wfa": {"ikutwfa", "wfa"},
    "status_pegawai": {"statuspegawai", "statuskepegawaian", "pnspppk", "jenispegawai", "status"},
}
MAKS_BARIS_IMPOR = 2000


def _nrm(x) -> str:
    return re.sub(r"[^a-z0-9]", "", str(x).lower())


def _teks(v) -> str:
    """Isi sel jadi teks rapi. Angka bulat (mis. NIP tersimpan sebagai angka) tidak diberi .0."""
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return " ".join(str(v).split())


def _tgl_impor(v):
    """(tanggal | None, salah?). Menerima sel tanggal Excel, DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD."""
    if v is None or (not isinstance(v, str) and pd.isna(v)) or str(v).strip() == "":
        return None, False
    if isinstance(v, date) and not hasattr(v, "hour"):
        return v, False
    if hasattr(v, "date") and not isinstance(v, str):
        return v.date(), False
    t = str(v).strip().split(" ")[0]
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", t)
    if m:
        y, mo, d = (int(x) for x in m.groups())
    else:
        m = re.match(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})$", t)
        if not m:
            return None, True
        d, mo, y = (int(x) for x in m.groups())
    try:
        return date(y, mo, d), False
    except ValueError:
        return None, True
    return None, True


def _pilih_nilai(v: str, daftar: list):
    """Cocokkan v ke salah satu isi daftar tanpa peduli huruf besar/kecil dan spasi."""
    kunci = _nrm(v)
    return next((x for x in daftar if _nrm(x) == kunci), None)


def _ya_tidak(v: str):
    t = v.strip().lower()
    if not t:
        return None, False
    if t in ("ya", "y", "aktif", "ikut", "1", "true", "yes"):
        return "Ya", False
    if t in ("tidak", "t", "nonaktif", "tidak aktif", "tidak ikut", "0", "false", "no"):
        return "Tidak", False
    return None, True


def baca_excel_pegawai(berkas):
    """Baca sheet pertama. Kembalikan (daftar baris dict berkunci kode kolom, pesan galat atau None)."""
    try:
        df = pd.read_excel(berkas, dtype=object, engine="openpyxl")
    except Exception as e:
        return [], f"File tidak bisa dibaca sebagai Excel (.xlsx): {e}"
    peta = {}
    for kol in df.columns:
        for kode, alias in ALIAS_IMPOR.items():
            if _nrm(kol) in alias and kode not in peta.values():
                peta[kol] = kode
                break
    if "nama" not in peta.values():
        return [], ("Kolom Nama tidak ditemukan. Kolom yang terbaca: "
                    + ", ".join(str(c) for c in df.columns) + ". Pakai templat dari tombol Unduh.")
    df = df.dropna(how="all")
    if len(df) > MAKS_BARIS_IMPOR:
        return [], f"Terlalu banyak baris ({len(df)}). Maksimal {MAKS_BARIS_IMPOR} baris per impor."
    baris = []
    for no, (_, r) in enumerate(df.iterrows(), start=2):          # baris Excel: header = 1
        isi = {kode: r[kol] for kol, kode in peta.items()}
        isi["_baris"] = no
        baris.append(isi)
    return baris, None


def rencana_impor(baris: list, perbarui: bool, buat_unit: bool) -> list:
    """Periksa semua baris tanpa mengubah data. Tiap hasil: status Baru/Perbarui/Lewati/Galat."""
    by_nip, by_nama = {}, {}
    for p in D["pekerja"]:
        if p.get("nip"):
            by_nip["".join(str(p["nip"]).split())] = p
        by_nama.setdefault(" ".join(p["nama"].lower().split()), []).append(p)
    bid_nama = {_nrm(b["nama"]): b for b in D["bidang"]}
    hasil, terlihat = [], set()
    bidang_baru, sub_baru = set(), set()
    for r in baris:
        cat, galat = [], []
        nama = _teks(r.get("nama"))
        nip = "".join(_teks(r.get("nip")).split())
        if not nama:
            galat.append("Nama kosong")
        if nip and not nip.isdigit():
            galat.append("NIP harus angka (format kolom NIP sebagai Teks di Excel)")
        if len(nip) > 15 and (not isinstance(r.get("nip"), str) or re.fullmatch(r"\d+0{3,}", nip)):
            cat.append("NIP tersimpan sebagai angka di Excel, mungkin terpotong: periksa, "
                       "dan format kolom NIP sebagai Teks")
        v = {"nama": nama, "nip": nip, "gelar_depan": _teks(r.get("gelar_depan")),
             "gelar_belakang": _teks(r.get("gelar_belakang")), "jabatan": _teks(r.get("jabatan"))}
        for kode, daftar, label in (("golongan", GOLONGAN, "Golongan"), ("eselon", ESELON, "Eselon"),
                                    ("jenis_jabatan", JENIS_JABATAN, "Jenis jabatan")):
            t = _teks(r.get(kode))
            if t:
                cocok = _pilih_nilai(t, daftar)
                if cocok:
                    v[kode] = cocok
                else:
                    galat.append(f"{label} '{t}' tidak dikenal")
        t = _teks(r.get("status_pegawai"))
        if t:
            sp = "PNS" if _nrm(t) in ("pns", "cpns") else ("PPPK" if _nrm(t) == "pppk" else None)
            if sp:
                v["status_pegawai"] = sp
            else:
                galat.append(f"Status pegawai '{t}' tidak dikenal (isi PNS atau PPPK)")
        if v.get("golongan") and v.get("status_pegawai") and \
                v["golongan"].startswith("PPPK") != (v["status_pegawai"] == "PPPK"):
            galat.append(f"Golongan {v['golongan']} tidak cocok dengan status {v['status_pegawai']}")
        t = _teks(r.get("jk")).lower()
        if t:
            if t in ("l", "laki-laki", "laki laki", "laki", "pria"):
                v["jk"] = "L"
            elif t in ("p", "perempuan", "wanita"):
                v["jk"] = "P"
            else:
                galat.append(f"Jenis kelamin '{t}' tidak dikenal (isi L atau P)")
        for kode, label in (("tgl_masuk", "Tanggal masuk"), ("tgl_pensiun", "Tanggal pensiun")):
            d, salah = _tgl_impor(r.get(kode))
            if salah:
                galat.append(f"{label} tidak terbaca (pakai format DD/MM/YYYY)")
            elif d:
                v[kode] = d.isoformat()
        if v.get("tgl_masuk") and v.get("tgl_pensiun") and v["tgl_pensiun"] <= v["tgl_masuk"]:
            galat.append("Tanggal pensiun harus setelah tanggal masuk")
        for kode, label in (("aktif", "Aktif"), ("ikut_wfa", "Ikut WFA")):
            nilai, salah = _ya_tidak(_teks(r.get(kode)))
            if salah:
                galat.append(f"{label} harus Ya atau Tidak")
            elif nilai:
                v[kode] = nilai
        # bidang dan sub bidang
        bn, sn = _teks(r.get("bidang")), _teks(r.get("subbidang"))
        if sn and not bn:
            galat.append("Sub bidang diisi tapi Bidang kosong")
        if bn:
            b = bid_nama.get(_nrm(bn))
            if b:
                v["bidang"] = b["nama"]
            elif buat_unit:
                v["bidang"] = bn
                bidang_baru.add(bn)
                cat.append(f"bidang baru: {bn}")
            else:
                galat.append(f"Bidang '{bn}' belum ada")
        if sn and bn and "bidang" in v:
            b = bid_nama.get(_nrm(bn))
            ada = b and any(x["bidang"] == b["id"] and _nrm(x["nama"]) == _nrm(sn) for x in D["subbidang"])
            if ada:
                v["subbidang"] = next(x["nama"] for x in D["subbidang"]
                                      if x["bidang"] == b["id"] and _nrm(x["nama"]) == _nrm(sn))
            elif buat_unit:
                v["subbidang"] = sn
                sub_baru.add((bn, sn))
                cat.append(f"sub bidang baru: {sn}")
            else:
                galat.append(f"Sub bidang '{sn}' belum ada di bidang {bn}")
        # cocokkan dengan pegawai yang sudah ada
        cocok_p = None
        if nama and not galat:
            kunci = nip or " ".join(nama.lower().split())
            if kunci in terlihat:
                galat.append("Dobel di dalam file ini")
            terlihat.add(kunci)
            if nip:
                cocok_p = by_nip.get(nip)
                if not cocok_p and by_nama.get(" ".join(nama.lower().split())):
                    cat.append("nama sudah ada dengan NIP lain")
            else:
                sama = by_nama.get(" ".join(nama.lower().split()), [])
                if len(sama) > 1:
                    galat.append("Nama sama dengan beberapa pegawai, isi NIP untuk membedakan")
                elif sama:
                    cocok_p = sama[0]
        if galat:
            status = "Galat"
        elif cocok_p and not perbarui:
            status = "Lewati"
            cat.append("sudah ada")
        elif cocok_p:
            status = "Perbarui"
        else:
            status = "Baru"
        hasil.append({"baris": r["_baris"], "status": status, "nilai": v, "cocok": cocok_p,
                      "catatan": "; ".join(galat + cat)})
    return hasil


def terapkan_impor(rencana: list) -> int:
    """Ubah D sesuai rencana (hanya baris Baru/Perbarui). Kembalikan jumlah yang diproses."""
    def id_bidang(nama):
        b = next((x for x in D["bidang"] if _nrm(x["nama"]) == _nrm(nama)), None)
        if not b:
            b = {"id": uuid.uuid4().hex[:8], "nama": nama}
            D["bidang"].append(b)
        return b["id"]

    def id_sub(bid, nama):
        x = next((y for y in D["subbidang"] if y["bidang"] == bid and _nrm(y["nama"]) == _nrm(nama)), None)
        if not x:
            x = {"id": uuid.uuid4().hex[:8], "nama": nama, "bidang": bid}
            D["subbidang"].append(x)
        return x["id"]

    n = 0
    for r in rencana:
        if r["status"] not in ("Baru", "Perbarui"):
            continue
        v = dict(r["nilai"])
        isi = {k: v[k] for k in ("nama", "nip", "gelar_depan", "gelar_belakang", "golongan", "eselon",
                                 "jenis_jabatan", "jabatan", "jk", "tgl_masuk", "tgl_pensiun",
                                 "status_pegawai") if v.get(k)}
        if v.get("bidang"):
            isi["bidang"] = id_bidang(v["bidang"])
            if v.get("subbidang"):
                isi["subbidang"] = id_sub(isi["bidang"], v["subbidang"])
        if r["status"] == "Baru":
            p = {"id": uuid.uuid4().hex[:8]}
            D["pekerja"].append(p)
        else:
            p = r["cocok"]
            if isi.get("bidang") and p.get("bidang") != isi["bidang"] and "subbidang" not in isi:
                p.pop("subbidang", None)          # pindah bidang: sub bidang lama tidak berlaku lagi
        p.update(isi)
        for kode, kunci in (("aktif", "aktif"), ("ikut_wfa", "ikut_wfa")):
            if v.get(kode) == "Tidak":
                p[kunci] = False
            elif v.get(kode) == "Ya":
                p.pop(kunci, None)
        n += 1
    return n


def buat_excel_pegawai(dengan_data: bool) -> bytes:
    """Templat impor (kosong, dengan satu contoh) atau data pegawai saat ini dalam format yang sama."""
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws = wb.active
    ws.title = "Pegawai"
    ws.append([j for _, j in KOLOM_IMPOR])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2B7A57")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if dengan_data:
        for p in D["pekerja"]:
            sb = sub_dari(p)
            ws.append([str(p.get("nip", "")), p.get("gelar_depan", ""), p["nama"], p.get("gelar_belakang", ""),
                       p.get("golongan", ""), p.get("eselon", ""), p.get("jenis_jabatan", ""),
                       p.get("jabatan", ""), nama_bidang(p) if p.get("bidang") in
                       {b["id"] for b in D["bidang"]} else "", sb["nama"] if sb else "",
                       JK_NAMA.get(p.get("jk", ""), ""),
                       ke_tgl(p.get("tgl_masuk")), ke_tgl(p.get("tgl_pensiun")),
                       "Tidak" if not aktif(p) else "Ya", "Ya" if ikut_wfa(p) else "Tidak",
                       status_peg(p)])
    else:
        ws.append(["198501012010011001", "Dr.", "Budi Santoso", "S.T., M.T.", "III/c", "Non eselon",
                   "Fungsional", "Analis Kebijakan", "", "", "Laki-laki", date(2010, 1, 1), None, "Ya", "Ya", "PNS"])
    akhir = max(ws.max_row, 300)
    for kol in (1,):                                     # NIP sebagai teks
        for r in range(2, akhir + 1):
            ws.cell(r, kol).number_format = "@"
    for kol in (12, 13):
        for r in range(2, akhir + 1):
            ws.cell(r, kol).number_format = "DD/MM/YYYY"
    # daftar pilihan di sheet kedua
    dv = wb.create_sheet("Daftar pilihan")
    daftar = [("Golongan", GOLONGAN, 5), ("Eselon", ESELON, 6), ("Jenis jabatan", JENIS_JABATAN, 7),
              ("Jenis kelamin", ["Laki-laki", "Perempuan"], 11), ("Aktif", ["Ya", "Tidak"], 14),
              ("Ikut WFA", ["Ya", "Tidak"], 15), ("Status pegawai", STATUS_PEG, 16), ("Bidang", [b["nama"] for b in D["bidang"]], 9)]
    for i, (judul, isi, kol_data) in enumerate(daftar, start=1):
        dv.cell(1, i, judul).font = Font(bold=True)
        for j, x in enumerate(isi, start=2):
            dv.cell(j, i, x)
        dv.column_dimensions[get_column_letter(i)].width = 16
        if isi:
            huruf = get_column_letter(i)
            v = DataValidation(type="list", formula1=f"='Daftar pilihan'!${huruf}$2:${huruf}${len(isi) + 1}",
                               allow_blank=True, errorStyle="warning" if judul == "Bidang" else "stop")
            ws.add_data_validation(v)
            v.add(f"{get_column_letter(kol_data)}2:{get_column_letter(kol_data)}{akhir}")
    lebar = [20, 10, 28, 16, 12, 12, 14, 26, 20, 20, 14, 15, 15, 8, 10, 14]
    for i, w in enumerate(lebar, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "D2"
    pt = wb.create_sheet("Petunjuk")
    for t in ["Petunjuk impor pegawai",
              "1. Isi sheet Pegawai, satu pegawai per baris. Hanya kolom Nama yang wajib.",
              "2. Jangan ubah judul kolom di baris pertama. Urutan kolom boleh berbeda.",
              "3. NIP: isi sebagai teks, hanya angka. Kolom NIP sudah diformat teks, supaya angka panjang tidak terpotong.",
              "4. Tanggal: format DD/MM/YYYY. Tanggal pensiun = hari pertama sudah tidak bekerja.",
              "5. Jenis kelamin: Laki-laki atau Perempuan (L atau P juga bisa).",
              "6. Bidang dan Sub bidang: tulis namanya. Yang belum ada bisa dibuat otomatis saat impor.",
              "7a. Status pegawai: PNS atau PPPK. Kosong = ditebak dari golongan (golongan PPPK = PPPK).",
              "7. Aktif dan Ikut WFA: Ya atau Tidak. Kosong berarti tidak diubah (pegawai baru: Ya).",
              "8. Pegawai dicocokkan lewat NIP; kalau NIP kosong, lewat nama. Sel kosong tidak menghapus data lama."]:
        pt.append([t])
    pt["A1"].font = Font(bold=True, size=13)
    pt.column_dimensions["A"].width = 110
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def halaman_pegawai():
    by_id = {p["id"]: p for p in D["pekerja"]}
    mode = st.session_state.get("pg_mode")          # None (daftar), "baru", atau id pegawai
    if mode not in (None, "baru") and mode not in by_id:
        mode = None
    with st.container(key="kartu_pegawai"):
        if not mode:
            st.button("Tambah pegawai", type="primary", key="pg_tambah",
                      on_click=atur, args=("pg_mode", "baru"))
            with st.expander("Impor dari Excel", icon=":material/upload_file:"):
                st.caption("Unduh templat, isi, lalu unggah. Sebelum disimpan, Anda bisa memeriksa dulu "
                           "hasilnya di tabel pratinjau.")
                u1, u2 = st.columns(2)
                u1.download_button("Unduh templat kosong", buat_excel_pegawai(False),
                                   file_name="templat-pegawai.xlsx", icon=":material/download:",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                u2.download_button("Unduh data pegawai saat ini", buat_excel_pegawai(True),
                                   file_name="data-pegawai.xlsx", icon=":material/download:",
                                   disabled=not D["pekerja"],
                                   help="Format sama dengan templat. Bisa diedit lalu diimpor lagi untuk "
                                        "memperbarui banyak pegawai sekaligus.",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                berkas = st.file_uploader("File Excel (.xlsx)", type=["xlsx"], key=f"imp_berkas_{versi()}")
                o1, o2 = st.columns(2)
                perbarui = o1.checkbox("Perbarui pegawai yang sudah ada", value=False, key="imp_perbarui",
                                       help="Mati: pegawai yang sudah ada dilewati. Hidup: kolom yang diisi di "
                                            "Excel menimpa data lama, kolom kosong tidak mengubah apa pun.")
                buat_unit = o2.checkbox("Buat bidang dan sub bidang yang belum ada", value=True, key="imp_buat")
                if berkas is not None:
                    baris, galat_file = baca_excel_pegawai(berkas)
                    if galat_file:
                        st.error(galat_file)
                    elif not baris:
                        st.warning("Tidak ada baris data di file itu.")
                    else:
                        rencana = rencana_impor(baris, perbarui, buat_unit)
                        jml = {k: sum(r["status"] == k for r in rencana) for k in ("Baru", "Perbarui", "Lewati", "Galat")}
                        st.markdown(f"**{jml['Baru']}** baru · **{jml['Perbarui']}** diperbarui · "
                                    f"**{jml['Lewati']}** dilewati · **{jml['Galat']}** galat")
                        st.dataframe(pd.DataFrame([
                            {"Baris": r["baris"], "Status": r["status"], "Nama": r["nilai"].get("nama", ""),
                             "NIP": r["nilai"].get("nip", ""), "Catatan": r["catatan"]} for r in rencana]),
                            hide_index=True, use_container_width=True)
                        if jml["Galat"]:
                            st.caption("Baris bergalat tidak ikut diimpor. Perbaiki di Excel lalu unggah ulang, "
                                       "atau lanjutkan untuk baris yang baik saja.")
                        n_ok = jml["Baru"] + jml["Perbarui"]
                        if st.button(f"Impor {n_ok} pegawai", type="primary", disabled=n_ok == 0, key="imp_jalan"):
                            n = terapkan_impor(rencana)
                            selesai_simpan(f"Impor {n} pegawai dari Excel")
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
                     ("jabatan", "Jabatan"), ("bidang", "Bidang / Sub bidang")]
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
                "bidang": lambda x: (nama_unit(x).lower(), x["nama"].lower()),
            }[kini]
            urut = sorted(D["pekerja"], key=kunci_urut, reverse=not naik)
            if cari:
                urut = [x for x in urut if cari in " ".join(
                    [x["nama"], str(x.get("nip", "")), x.get("jabatan", ""), nama_unit(x), status_peg(x)]).lower()]
                if not urut:
                    st.info("Tidak ada pegawai yang cocok dengan pencarian.")
            for no, p in enumerate(urut, 1):
                st.markdown('<div class="garis"></div>', unsafe_allow_html=True)
                k = st.columns(lebar, vertical_alignment="center")
                k[0].write(f"{no}.")
                k[1].write(p.get("nip", ""))
                k[2].markdown(f"{html.escape(nama_lengkap(p))}"
                              + (f" · {status_peg(p)}" if status_peg(p) else "")
                              + ("" if aktif(p) else " *(nonaktif)*")
                              + ("" if ikut_wfa(p) else " *(tidak WFA)*"))
                k[3].write(p.get("jabatan", ""))
                k[4].write(nama_unit(p) if D["bidang"] else "")
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
        # Bidang dan sub bidang di luar formulir, supaya pilihan sub bidang ikut berubah
        # begitu bidang diganti (isi formulir biasa baru terbaca saat Simpan).
        bid = sub = ""
        if D["bidang"]:
            peta = {b["id"]: b["nama"] for b in D["bidang"]}
            opsi = [""] + list(peta)
            q1, q2 = st.columns(2)
            bid = q1.selectbox("Bidang", opsi, index=idx(opsi, p.get("bidang", "")),
                               format_func=lambda i: TANPA if not i else peta[i],
                               key=f"pg_bid_{mode}_{versi()}")
            subs = [x for x in D["subbidang"] if (x["bidang"] == bid if bid else x["bidang"] in peta)]
            if subs:
                ops = [""] + [x["id"] for x in subs]
                nama_s = {x["id"]: (x["nama"] if bid else f"{peta[x['bidang']]} › {x['nama']}") for x in subs}
                awal = p.get("subbidang", "") if sub_dari(p) and sub_dari(p)["id"] in nama_s else ""
                sub = q2.selectbox("Sub bidang (boleh kosong)", ops, index=idx(ops, awal),
                                   format_func=lambda i: "Tanpa sub bidang" if not i else nama_s[i],
                                   key=f"pg_sub_{mode}_{versi()}_{bid or 'semua'}")
            elif bid:
                q2.selectbox("Sub bidang (boleh kosong)", ["Belum ada sub bidang di bidang ini"],
                             disabled=True, key=f"pg_subkosong_{mode}_{versi()}_{bid}")
        with st.form(f"form_pg_{mode}_{versi()}"):
            k1, k1b, k2 = st.columns([3, 1.6, 2])
            nip = k1.text_input("NIP Pegawai", value=p.get("nip", ""), placeholder="NIP Pegawai")
            stp_ops = [""] + STATUS_PEG
            stp = k1b.selectbox("Status pegawai", stp_ops, index=idx(stp_ops, status_peg(p)),
                                format_func=lambda v: v or "Pilih...")
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
            e1, e2, e3 = st.columns([1.6, 1.5, 1.5])
            jk_ops = ["", "L", "P"]
            jk = e1.selectbox("Jenis kelamin", jk_ops, index=idx(jk_ops, p.get("jk", "")),
                              format_func=lambda i: JK_NAMA.get(i, "Pilih..."))
            batas = dict(min_value=date(1940, 1, 1), max_value=date(2100, 12, 31), format="DD/MM/YYYY")
            t_masuk = e2.date_input("Tanggal masuk", value=ke_tgl(p.get("tgl_masuk")), **batas)
            t_pensiun = e3.date_input("Tanggal pensiun", value=ke_tgl(p.get("tgl_pensiun")), **batas,
                                      help="Hari pertama sudah tidak bekerja (TMT pensiun). "
                                           "Kosongkan kalau belum ada.")
            kosong_m = kosong_k = False
            if p.get("tgl_masuk") or p.get("tgl_pensiun"):
                z1, z2 = st.columns(2)
                kosong_m = z1.checkbox("Kosongkan tanggal masuk") if p.get("tgl_masuk") else False
                kosong_k = z2.checkbox("Kosongkan tanggal pensiun") if p.get("tgl_pensiun") else False
            wfa_v = st.radio("Ikut WFA", ["Ya", "Tidak"], index=0 if ikut_wfa(p) else 1,
                             horizontal=True,
                             help="Pilih Tidak untuk pegawai yang tidak bekerja WFA (misalnya beda "
                                  "divisi). Tidak dihitung di rekap WFA, tetapi tetap di triwulan.")
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
                elif gol and stp and (gol.startswith("PPPK") != (stp == "PPPK")):
                    st.error(f"Golongan {gol} tidak cocok dengan status {stp}.")
                elif t_masuk and t_pensiun and not kosong_m and not kosong_k and t_pensiun <= t_masuk:
                    st.error("Tanggal pensiun harus setelah tanggal masuk.")
                elif sub and bid and next(x for x in D["subbidang"] if x["id"] == sub)["bidang"] != bid:
                    st.error("Sub bidang yang dipilih bukan bagian dari bidang di atas.")
                else:
                    if sub and not bid:
                        bid = next(x for x in D["subbidang"] if x["id"] == sub)["bidang"]
                    baru = dict(p) if mode != "baru" else {"id": uuid.uuid4().hex[:8]}
                    isi = {"nama": nama, "nip": nip, "gelar_depan": gd.strip(),
                           "gelar_belakang": gb.strip(), "golongan": gol, "eselon": esl,
                           "jenis_jabatan": jns, "jabatan": jab.strip(), "bidang": bid,
                           "subbidang": sub, "jk": jk, "status_pegawai": stp,
                           "tgl_masuk": "" if kosong_m or not t_masuk else t_masuk.isoformat(),
                           "tgl_pensiun": "" if kosong_k or not t_pensiun else t_pensiun.isoformat()}
                    for kunci, v in isi.items():
                        if v or kunci == "nama":
                            baru[kunci] = v
                        else:
                            baru.pop(kunci, None)
                    if aktif_v == "Tidak":
                        baru["aktif"] = False
                    else:
                        baru.pop("aktif", None)
                    if wfa_v == "Tidak":
                        baru["ikut_wfa"] = False
                    else:
                        baru.pop("ikut_wfa", None)
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
                    if kunci == "bidang":   # sub bidang di bawahnya ikut hilang
                        D["subbidang"] = [y for y in D["subbidang"] if y["bidang"] != x["id"]]
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


def halaman_subbidang():
    """Sub bidang selalu berada di bawah satu bidang."""
    if not D["bidang"]:
        st.info("Buat bidang dulu di menu Bidang, lalu tambahkan sub bidangnya di sini.")
        return
    peta = {b["id"]: b["nama"] for b in D["bidang"]}
    with st.expander(f"Sub bidang ({len(D['subbidang'])})", expanded=True):
        st.caption("Sub bidang berada di bawah satu bidang. Setelah ditambah, pilih sub bidang "
                   "di formulir pegawai. Menghapus sub bidang tidak menghapus pegawainya.")
        for b in D["bidang"]:
            milik = [x for x in D["subbidang"] if x["bidang"] == b["id"]]
            st.markdown(f'<div class="bidang">{html.escape(b["nama"])} · {len(milik)} sub bidang</div>',
                        unsafe_allow_html=True)
            if not milik:
                st.caption("Belum ada sub bidang.")
            for x in milik:
                c1, c2, c3 = st.columns([5, 1.8, 1.6], vertical_alignment="center")
                if st.session_state.get("edit_sub") == x["id"]:
                    baru = c1.text_input("Nama", value=x["nama"], key=f"nm_sub_{x['id']}",
                                         label_visibility="collapsed")
                    c3.button("Batal", key=f"bt_sub_{x['id']}", on_click=atur, args=("edit_sub", None))
                    if c2.button("Simpan", key=f"sv_sub_{x['id']}", type="primary"):
                        baru = baru.strip()
                        if not baru:
                            st.error("Nama tidak boleh kosong.")
                        elif ada_kembar([y["nama"] for y in milik if y["id"] != x["id"]] + [baru]):
                            st.error("Nama itu sudah ada di bidang ini.")
                        else:
                            x["nama"] = baru
                            selesai_simpan("Nama diubah.", edit_sub=None)
                elif st.session_state.get("hapus_sub") == x["id"]:
                    n_p = sum(1 for p in D["pekerja"] if p.get("subbidang") == x["id"])
                    c1.write(f"Hapus **{x['nama']}**?" + (f" ({n_p} pegawai jadi tanpa sub bidang)" if n_p else ""))
                    c3.button("Batal", key=f"bh_sub_{x['id']}", on_click=atur, args=("hapus_sub", None))
                    if c2.button("Ya, hapus", key=f"yh_sub_{x['id']}", type="primary"):
                        D["subbidang"] = [y for y in D["subbidang"] if y["id"] != x["id"]]
                        for p in D["pekerja"]:
                            if p.get("subbidang") == x["id"]:
                                p.pop("subbidang", None)
                        selesai_simpan("Dihapus.", hapus_sub=None)
                else:
                    c1.write(x["nama"])
                    c2.button("Ubah nama", key=f"ub_sub_{x['id']}", on_click=atur, args=("edit_sub", x["id"]))
                    c3.button("Hapus", key=f"hp_sub_{x['id']}", on_click=atur, args=("hapus_sub", x["id"]))
        with st.form("tambah_sub", clear_on_submit=True):
            f1, f2 = st.columns([2, 3])
            induk = f1.selectbox("Di bawah bidang", list(peta), format_func=lambda i: peta[i])
            nama = f2.text_input("Nama sub bidang", placeholder="Nama baru")
            if st.form_submit_button("Tambah sub bidang"):
                nama = nama.strip()
                if not nama:
                    st.error("Nama tidak boleh kosong.")
                elif ada_kembar([y["nama"] for y in D["subbidang"] if y["bidang"] == induk] + [nama]):
                    st.error("Nama itu sudah ada di bidang ini.")
                else:
                    D["subbidang"].append({"id": uuid.uuid4().hex[:8], "nama": nama, "bidang": induk})
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


# ------------------------------------------------------------ realisasi anggaran
BLN3 = [b[:3] for b in BULAN]
TANPA_PROG, TANPA_KEG = "(Tanpa program)", "(Tanpa kegiatan)"
ALIAS_BULAN = {m: {_nrm(BULAN[m - 1][:3]), _nrm(BULAN[m - 1])} for m in range(1, 13)}
ALIAS_BULAN[5] |= {"may"}
ALIAS_BULAN[8] |= {"agt", "agst", "aug"}
ALIAS_BULAN[10] |= {"oct"}
ALIAS_BULAN[12] |= {"dec"}
ALIAS_ANGGARAN = {"kode": {"kode", "kodesubkegiatan", "kodekegiatan"},
                  "program": {"program", "namaprogram"},
                  "kegiatan": {"kegiatan", "namakegiatan"},
                  "nama": {"subkegiatan", "namasubkegiatan", "uraian", "nama"},
                  "bidang": {"bidang", "unitkerja"},
                  "pagu": {"pagu", "paguanggaran", "anggaran"}}


def rp(n) -> str:
    return "Rp " + f"{int(round(n)):,}".replace(",", ".")


def rp_ringkas(n) -> str:
    """Untuk kartu: Rp 1,48 miliar / Rp 520 juta / Rp 950.000."""
    a = abs(n)
    for batas, satuan in ((1e12, "triliun"), (1e9, "miliar"), (1e6, "juta")):
        if a >= batas:
            return f"Rp {n / batas:,.2f} {satuan}".replace(",", "X").replace(".", ",").replace("X", ".")
    return rp(n)


def _angka(v):
    """Sel Excel -> angka rupiah (float) | None kalau kosong. Salah format -> ValueError."""
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = re.sub(r"(?i)rp\.?|\s", "", str(v))
    if not t:
        return None
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    elif re.fullmatch(r"-?\d{1,3}(,\d{3})+", t):
        t = t.replace(",", "")
    else:
        t = t.replace(",", ".")
    return float(t)


def real_sd(k: dict, bulan: int) -> float:
    return sum(k.get("real", {}).get(str(m), 0) or 0 for m in range(1, bulan + 1))


def persen_serap(real: float, pagu: float) -> float:
    return round(real / pagu * 100, 1) if pagu else 0.0


def baca_excel_anggaran(berkas):
    try:
        df = pd.read_excel(berkas, dtype=object, engine="openpyxl")
    except Exception as e:
        return [], f"File tidak bisa dibaca sebagai Excel (.xlsx): {e}"
    peta = {}                                    # kolom Excel -> "kode"/"nama"/.../("bln", m)
    for kol in df.columns:
        n = _nrm(kol)
        for kode, alias in ALIAS_ANGGARAN.items():
            if n in alias and kode not in peta.values():
                peta[kol] = kode
                break
        else:
            for m, alias in ALIAS_BULAN.items():
                if n in alias and ("bln", m) not in peta.values():
                    peta[kol] = ("bln", m)
                    break
    if "nama" not in peta.values() and "kegiatan" in peta.values():
        # file tanpa kolom Sub kegiatan: kolom Kegiatan dianggap nama sub kegiatan
        peta = {k: ("nama" if v == "kegiatan" else v) for k, v in peta.items()}
    if "nama" not in peta.values():
        return [], ("Kolom Sub kegiatan tidak ditemukan. Kolom yang terbaca: "
                    + ", ".join(str(c) for c in df.columns) + ". Pakai templat dari tombol Unduh.")
    df = df.dropna(how="all")
    if len(df) > MAKS_BARIS_IMPOR:
        return [], f"Terlalu banyak baris ({len(df)}). Maksimal {MAKS_BARIS_IMPOR} baris per impor."
    baris = []
    for no, (_, r) in enumerate(df.iterrows(), start=2):
        isi = {"_baris": no, "bln": {}}
        for kol, kode in peta.items():
            if isinstance(kode, tuple):
                isi["bln"][kode[1]] = r[kol]
            else:
                isi[kode] = r[kol]
        baris.append(isi)
    return baris, None


def rencana_anggaran(baris: list, tahun: int, perbarui: bool, buat_bidang: bool, kumulatif: bool) -> list:
    ada = [k for k in D["anggaran"] if k["tahun"] == tahun]
    kunci_h = lambda k: (_nrm(k.get("program", "")), _nrm(k.get("kegiatan", "")), _nrm(k["nama"]))
    by_kode = {_nrm(k["kode"]): k for k in ada if k.get("kode")}
    by_nama = {kunci_h(k): k for k in ada}
    bid_nama = {_nrm(b["nama"]): b["nama"] for b in D["bidang"]}
    hasil, terlihat = [], set()
    for r in baris:
        cat, galat = [], []
        nama, kode = _teks(r.get("nama")), _teks(r.get("kode"))
        if not nama:
            galat.append("Nama sub kegiatan kosong")
        v = {"nama": nama, "kode": kode, "program": _teks(r.get("program")), "kegiatan": _teks(r.get("kegiatan"))}
        try:
            pagu = _angka(r.get("pagu"))
            if pagu is not None:
                if pagu < 0:
                    galat.append("Pagu tidak boleh negatif")
                v["pagu"] = int(round(pagu))
        except ValueError:
            galat.append("Pagu bukan angka")
        bn = _teks(r.get("bidang"))
        if bn:
            if _nrm(bn) in bid_nama:
                v["bidang"] = bid_nama[_nrm(bn)]
            elif buat_bidang:
                v["bidang"] = bn
                cat.append(f"bidang baru: {bn}")
            else:
                galat.append(f"Bidang '{bn}' belum ada")
        real, prev = {}, 0.0
        for m in range(1, 13):
            try:
                x = _angka(r["bln"].get(m))
            except ValueError:
                galat.append(f"{BLN3[m - 1]} bukan angka")
                continue
            if x is None:
                continue
            if kumulatif:
                x, prev = x - prev, x
                if x < 0:
                    galat.append(f"Kumulatif {BLN3[m - 1]} lebih kecil dari bulan sebelumnya")
                    continue
            elif x < 0:
                galat.append(f"{BLN3[m - 1]} tidak boleh negatif")
                continue
            real[str(m)] = int(round(x))
        v["real"] = real
        cocok = None
        if nama and not galat:
            kunci_i = (_nrm(v["program"]), _nrm(v["kegiatan"]), _nrm(nama))
            kunci = _nrm(kode) or kunci_i
            if kunci in terlihat:
                galat.append("Dobel di dalam file ini")
            terlihat.add(kunci)
            cocok = by_kode.get(_nrm(kode)) if kode else None
            if not cocok:
                cocok = by_nama.get(kunci_i)
        if galat:
            status = "Galat"
        elif cocok and not perbarui:
            status, _ = "Lewati", cat.append("sudah ada")
        elif cocok:
            status = "Perbarui"
        else:
            status = "Baru"
            if "pagu" not in v:
                cat.append("pagu kosong, dianggap 0")
        hasil.append({"baris": r["_baris"], "status": status, "nilai": v, "cocok": cocok,
                      "catatan": "; ".join(galat + cat)})
    return hasil


def terapkan_anggaran(rencana: list, tahun: int) -> int:
    n = 0
    for r in rencana:
        if r["status"] not in ("Baru", "Perbarui"):
            continue
        v = r["nilai"]
        bn = v.get("bidang")
        bid = ""
        if bn:
            b = next((x for x in D["bidang"] if _nrm(x["nama"]) == _nrm(bn)), None)
            if not b:
                b = {"id": uuid.uuid4().hex[:8], "nama": bn}
                D["bidang"].append(b)
            bid = b["id"]
        if r["status"] == "Baru":
            k = {"id": uuid.uuid4().hex[:8], "tahun": tahun, "kode": "", "nama": v["nama"],
                 "pagu": 0, "real": {}}
            D["anggaran"].append(k)
        else:
            k = r["cocok"]
        k["nama"] = v["nama"]
        for kk in ("kode", "program", "kegiatan"):
            if v.get(kk):
                k[kk] = v[kk]
        if "pagu" in v:
            k["pagu"] = v["pagu"]
        if bid:
            k["bidang"] = bid
        k.setdefault("real", {}).update(v["real"])
        n += 1
    return n


def buat_excel_anggaran(tahun: int, dengan_data: bool) -> bytes:
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws = wb.active
    ws.title = "Anggaran"
    ws.append(["Kode", "Program", "Kegiatan", "Sub kegiatan", "Bidang", "Pagu"] + BLN3)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2B7A57")
        c.alignment = Alignment(horizontal="center", vertical="center")
    peta = {b["id"]: b["nama"] for b in D["bidang"]}
    if dengan_data:
        for k in sorted((x for x in D["anggaran"] if x["tahun"] == tahun), key=lambda x: (x.get("kode", ""), x["nama"])):
            ws.append([k.get("kode", ""), k.get("program", ""), k.get("kegiatan", ""), k["nama"],
                       peta.get(k.get("bidang"), ""), k.get("pagu", 0)]
                      + [k.get("real", {}).get(str(m)) for m in range(1, 13)])
    else:
        ws.append(["1.01.02.2.01.0001", "Program Penunjang Urusan Pemerintahan",
                   "Perencanaan, Penganggaran, dan Evaluasi Kinerja", "Penyusunan dokumen perencanaan", "",
                   150000000, 10000000, 12500000, None, None, None, None, None, None, None, None, None, None])
    akhir = max(ws.max_row, 300)
    for r in range(2, akhir + 1):
        for c in range(6, 19):
            ws.cell(r, c).number_format = "#,##0"
    lebar = [20, 30, 36, 40, 20, 16] + [13] * 12
    for i, w in enumerate(lebar, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "E2"
    if D["bidang"]:
        dv = wb.create_sheet("Daftar bidang")
        dv.cell(1, 1, "Bidang").font = Font(bold=True)
        for j, b in enumerate(D["bidang"], start=2):
            dv.cell(j, 1, b["nama"])
        v = DataValidation(type="list", formula1=f"='Daftar bidang'!$A$2:$A${len(D['bidang']) + 1}",
                           allow_blank=True, errorStyle="warning")
        ws.add_data_validation(v)
        v.add(f"E2:E{akhir}")
    pt = wb.create_sheet("Petunjuk")
    for t in ["Petunjuk impor realisasi anggaran",
              "1. Satu baris = satu sub kegiatan (tempat anggaran diisi). Program dan Kegiatan diisi namanya, berulang di tiap baris. Hanya kolom Sub kegiatan yang wajib.",
              "2. Tahun dipilih di aplikasi saat impor, bukan di file.",
              "3. Kolom Jan sampai Des: isi angka rupiah. Pilih di aplikasi apakah angkanya "
              "realisasi bulan itu atau kumulatif sampai bulan itu.",
              "4. Bulan yang dikosongkan tidak mengubah data lama.",
              "5. Sub kegiatan dicocokkan lewat Kode; kalau Kode kosong, lewat Program + Kegiatan + nama sub kegiatan."]:
        pt.append([t])
    pt["A1"].font = Font(bold=True, size=13)
    pt.column_dimensions["A"].width = 110
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def halaman_anggaran():
    admin = adalah_admin()
    hari_ini = date.today()
    tahun_opsi = sorted({k["tahun"] for k in D["anggaran"]} | {hari_ini.year})
    with st.container(key="kartu_filter"):
        f1, f2, f3, f4, f5 = st.columns([1, 1.5, 1.3, 1.8, 2.2])
        th = f1.selectbox("Tahun", tahun_opsi, index=tahun_opsi.index(hari_ini.year), key="ang_tahun")
        awal_bln = hari_ini.month if th == hari_ini.year else 12
        sd = f2.selectbox("Realisasi sampai bulan", list(range(1, 13)), index=awal_bln - 1,
                          format_func=lambda m: BULAN[m - 1], key=f"ang_sd_{th}")
        mode = f3.radio("Grafik per", ["Bulan", "Triwulan"], horizontal=True, key="ang_mode")
        peta_b = {b["id"]: b["nama"] for b in D["bidang"]}
        bid_opsi = ["Semua bidang"] + [b["nama"] for b in D["bidang"]] + ([TANPA] if D["anggaran"] else [])
        bid_pilih = f4.selectbox("Bidang", bid_opsi, key="ang_bidang") if D["bidang"] else "Semua bidang"
        prog_nama = sorted({k.get("program") or TANPA_PROG for k in D["anggaran"] if k["tahun"] == th})
        prog_pilih = f5.selectbox("Program", ["Semua program"] + prog_nama, key=f"ang_prog_{th}")
    nama_tab = ["Rekap", "Isi dan ubah", "Impor Excel"] if admin else ["Rekap"]
    tabs = st.tabs(nama_tab)

    semua = [k for k in D["anggaran"] if k["tahun"] == th]
    daftar = [k for k in semua
              if (bid_pilih == "Semua bidang" or peta_b.get(k.get("bidang"), TANPA) == bid_pilih)
              and (prog_pilih == "Semua program" or (k.get("program") or TANPA_PROG) == prog_pilih)]

    with tabs[0]:
        if not daftar:
            st.info("Belum ada data anggaran untuk pilihan ini." + (
                " Tambahkan di tab Isi dan ubah, atau impor dari Excel." if admin else ""))
        else:
            pagu = sum(k.get("pagu", 0) for k in daftar)
            real = sum(real_sd(k, sd) for k in daftar)
            ser = persen_serap(real, pagu)
            st.markdown(
                '<div class="statcard"><div class="sc-kiri"><span class="tag">Anggaran</span>'
                f'<div class="sc-judul">Serapan {ser:.1f}%</div>'
                f'<div class="sc-ket">{len(daftar)} sub kegiatan, s.d. {BULAN[sd - 1]} {th}</div></div>'
                f'<div class="sc-stat"><div class="sc-lab">Pagu</div><div class="sc-val" title="{rp(pagu)}" style="font-size:1.25rem;white-space:nowrap">{rp_ringkas(pagu)}</div></div>'
                f'<div class="sc-stat"><div class="sc-lab">Realisasi</div><div class="sc-val g" title="{rp(real)}" style="font-size:1.25rem;white-space:nowrap">{rp_ringkas(real)}</div></div>'
                f'<div class="sc-stat"><div class="sc-lab">Sisa</div><div class="sc-val m" title="{rp(pagu - real)}" style="font-size:1.25rem;white-space:nowrap">{rp_ringkas(pagu - real)}</div></div>'
                '</div>', unsafe_allow_html=True)
            # grafik per periode
            if mode == "Bulan":
                per = [(BLN3[m - 1], m, m) for m in range(1, sd + 1)]
            else:
                per = [(f"TW {ROMAWI[q]}", 3 * q - 2, min(3 * q, sd)) for q in range(1, 5) if 3 * q - 2 <= sd]
            baris = []
            for nm, a, z in per:
                nilai = sum(k.get("real", {}).get(str(m), 0) or 0 for k in daftar for m in range(a, z + 1))
                baris.append({"Periode": nm, "Realisasi (Rp juta)": round(nilai / 1e6, 2),
                              "Serapan kumulatif (%)": min(persen_serap(sum(real_sd(k, z) for k in daftar), pagu), 100.0)})
            dfp = pd.DataFrame(baris)
            urutan = [b["Periode"] for b in baris]
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("**Realisasi per periode (Rp juta)**")
                st.vega_lite_chart(dfp, {"mark": {"type": "bar", "color": "#2b7a57"}, "encoding": {
                    "x": {"field": "Periode", "type": "nominal", "sort": urutan,
                          "axis": {"title": None, "labelAngle": 0}},
                    "y": {"field": "Realisasi (Rp juta)", "type": "quantitative", "axis": {"title": None}},
                    "tooltip": [{"field": "Periode"}, {"field": "Realisasi (Rp juta)", "format": ",.2f"}]},
                    "width": "container", "height": 280})
            with g2:
                st.markdown("**Serapan kumulatif (%)**")
                grafik_persen(dfp, "Periode", "Serapan kumulatif (%)", urut=urutan)
            # rekap bertingkat
            tingkat = st.radio("Rekap per", ["Program", "Kegiatan", "Sub kegiatan", "Bidang"],
                               horizontal=True, key="ang_tingkat")

            def kunci_t(k):
                prog, keg = k.get("program") or TANPA_PROG, k.get("kegiatan") or TANPA_KEG
                bid = peta_b.get(k.get("bidang"), TANPA)
                return {"Program": (prog,), "Kegiatan": (prog, keg), "Bidang": (bid,),
                        "Sub kegiatan": (k.get("kode", ""), prog, keg, k["nama"], bid)}[tingkat]

            kol_t = {"Program": ["Program"], "Kegiatan": ["Program", "Kegiatan"], "Bidang": ["Bidang"],
                     "Sub kegiatan": ["Kode", "Program", "Kegiatan", "Sub kegiatan", "Bidang"]}[tingkat]
            grup = {}
            for k in daftar:
                grup.setdefault(kunci_t(k), []).append(k)
            rb, label = [], []
            for kunci, ks in sorted(grup.items()):
                p_, r_ = sum(k.get("pagu", 0) for k in ks), sum(real_sd(k, sd) for k in ks)
                baris_t = dict(zip(kol_t, kunci))
                if tingkat != "Sub kegiatan":
                    baris_t["Jumlah sub kegiatan"] = len(ks)
                baris_t.update({"Pagu": p_, "Realisasi": r_, "Sisa": p_ - r_, "Serapan (%)": persen_serap(r_, p_)})
                rb.append(baris_t)
                label.append(" › ".join(kunci) if tingkat == "Kegiatan" else kunci[-1] if tingkat != "Sub kegiatan"
                             else kunci[3])
            dfb = pd.DataFrame(rb)
            st.dataframe(dfb, hide_index=True, use_container_width=True, height=min(620, (len(dfb) + 1) * 35 + 3),
                         column_config={c: st.column_config.NumberColumn(format="localized")
                                        for c in ("Pagu", "Realisasi", "Sisa")}
                                       | {"Serapan (%)": st.column_config.ProgressColumn(
                                           "Serapan (%)", format="%.1f%%", min_value=0, max_value=100)})
            dfg = pd.DataFrame({"Label": label, "Serapan (%)": dfb["Serapan (%)"]})
            dfg["Label"] = dfg["Label"] + dfg.groupby("Label").cumcount().map(lambda i: "" if i == 0 else f" ({i + 1})")
            grafik_persen(dfg, "Label", "Serapan (%)", horizontal=True, urut="-x",
                          tinggi=min(900, max(140, 34 * len(dfg))))

    if not admin:
        return
    with tabs[1]:
        st.caption(f"Tahun {th}. Satu baris = satu **sub kegiatan** (anggaran diisi di sini; program dan kegiatan "
                   "diisi namanya dan dijumlahkan otomatis di Rekap). Bisa tempel (paste) dari Excel. "
                   "Isi realisasi per bulan dengan jumlah belanja **bulan itu** (bukan kumulatif). "
                   "Baris baru ditambah lewat baris kosong di bawah tabel; hapus dengan memilih baris lalu "
                   "tombol hapus. Filter bidang di atas tidak berlaku di sini.")
        kolom_df = ["id", "Kode", "Program", "Kegiatan", "Sub kegiatan", "Bidang", "Pagu"] + BLN3
        data_ed = [{"id": k["id"], "Kode": k.get("kode", ""), "Program": k.get("program", ""),
                    "Kegiatan": k.get("kegiatan", ""), "Sub kegiatan": k["nama"],
                    "Bidang": peta_b.get(k.get("bidang"), ""), "Pagu": k.get("pagu", 0),
                    **{BLN3[m - 1]: k.get("real", {}).get(str(m)) for m in range(1, 13)}}
                   for k in sorted(semua, key=lambda x: (x.get("kode", ""), x["nama"]))]
        df_ed = pd.DataFrame(data_ed, columns=kolom_df)
        angka_cfg = lambda judul, **kw: st.column_config.NumberColumn(judul, min_value=0, step=1, format="localized", **kw)
        cfg = {"id": None, "Kode": st.column_config.TextColumn("Kode", width="small"),
               "Program": st.column_config.TextColumn("Program", width="medium"),
               "Kegiatan": st.column_config.TextColumn("Kegiatan", width="medium"),
               "Sub kegiatan": st.column_config.TextColumn("Sub kegiatan", width="medium", required=True),
               "Bidang": st.column_config.SelectboxColumn("Bidang", options=[b["nama"] for b in D["bidang"]],
                                                          width="medium"),
               "Pagu": angka_cfg("Pagu", width="medium")}
        cfg.update({b: angka_cfg(b, width="small") for b in BLN3})
        hasil = st.data_editor(df_ed, column_config=cfg, num_rows="dynamic", hide_index=True,
                               use_container_width=True, key=f"ed_ang_{th}_{versi()}")
        if st.button("Simpan perubahan", type="primary", key="ang_simpan"):
            galat, baru, kode_lihat = [], [], set()
            lama = {k["id"]: k for k in semua}
            bid_id = {b["nama"]: b["id"] for b in D["bidang"]}
            for i, r in hasil.iterrows():
                if r.drop("id").isna().all():
                    continue
                no = f"Baris {i + 1}"
                nama = "" if pd.isna(r["Sub kegiatan"]) else " ".join(str(r["Sub kegiatan"]).split())
                if not nama:
                    galat.append(f"{no}: nama sub kegiatan kosong")
                    continue
                kode = "" if pd.isna(r["Kode"]) else str(r["Kode"]).strip()
                if kode and _nrm(kode) in kode_lihat:
                    galat.append(f"{no}: kode {kode} dobel")
                kode_lihat.add(_nrm(kode))
                kid = None if pd.isna(r["id"]) else r["id"]
                k = dict(lama.get(kid, {"id": uuid.uuid4().hex[:8], "tahun": th}))
                teks_sel = lambda c: "" if pd.isna(r[c]) else " ".join(str(r[c]).split())
                k.update({"kode": kode, "nama": nama, "program": teks_sel("Program"),
                          "kegiatan": teks_sel("Kegiatan"),
                          "pagu": 0 if pd.isna(r["Pagu"]) else int(round(float(r["Pagu"])))})
                b = "" if pd.isna(r["Bidang"]) else r["Bidang"]
                if b:
                    k["bidang"] = bid_id.get(b, "")
                else:
                    k.pop("bidang", None)
                k["real"] = {str(m): int(round(float(r[BLN3[m - 1]]))) for m in range(1, 13)
                             if not pd.isna(r[BLN3[m - 1]])}
                baru.append(k)
            if galat:
                for g in galat:
                    st.error(g)
            else:
                D["anggaran"] = [k for k in D["anggaran"] if k["tahun"] != th] + baru
                selesai_simpan(f"Anggaran {th} diperbarui ({len(baru)} sub kegiatan)")

    with tabs[2]:
        st.caption(f"Impor ke tahun **{th}**. Unduh templat, isi, lalu unggah. Hasilnya bisa diperiksa di "
                   "pratinjau sebelum disimpan.")
        u1, u2 = st.columns(2)
        xl = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        u1.download_button("Unduh templat kosong", buat_excel_anggaran(th, False), file_name="templat-anggaran.xlsx",
                           icon=":material/download:", mime=xl)
        u2.download_button(f"Unduh data {th} saat ini", buat_excel_anggaran(th, True),
                           file_name=f"anggaran-{th}.xlsx", icon=":material/download:", mime=xl,
                           disabled=not semua)
        berkas = st.file_uploader("File Excel (.xlsx)", type=["xlsx"], key=f"ang_berkas_{versi()}")
        o1, o2 = st.columns(2)
        kum = o1.radio("Angka bulan (Jan sampai Des) di Excel adalah",
                       ["Realisasi bulan itu", "Kumulatif sampai bulan itu"], key="ang_kum") == "Kumulatif sampai bulan itu"
        perb = o2.checkbox("Perbarui sub kegiatan yang sudah ada", value=True, key="ang_perb",
                           help="Dicocokkan lewat Kode, atau Program + Kegiatan + nama sub kegiatan kalau Kode kosong. Sel kosong tidak mengubah data.")
        buat_b = o2.checkbox("Buat bidang yang belum ada", value=True, key="ang_buatb")
        if berkas is not None:
            baris, galat_file = baca_excel_anggaran(berkas)
            if galat_file:
                st.error(galat_file)
            elif not baris:
                st.warning("Tidak ada baris data di file itu.")
            else:
                rencana = rencana_anggaran(baris, th, perb, buat_b, kum)
                jml = {s_: sum(r["status"] == s_ for r in rencana) for s_ in ("Baru", "Perbarui", "Lewati", "Galat")}
                st.markdown(f"**{jml['Baru']}** baru · **{jml['Perbarui']}** diperbarui · "
                            f"**{jml['Lewati']}** dilewati · **{jml['Galat']}** galat")
                st.dataframe(pd.DataFrame([
                    {"Baris": r["baris"], "Status": r["status"], "Kode": r["nilai"].get("kode", ""),
                     "Program": r["nilai"].get("program", ""), "Kegiatan": r["nilai"].get("kegiatan", ""),
                     "Sub kegiatan": r["nilai"].get("nama", ""), "Pagu": r["nilai"].get("pagu"),
                     "Realisasi (jumlah bulan terisi)": sum(r["nilai"]["real"].values()),
                     "Catatan": r["catatan"]} for r in rencana]), hide_index=True, use_container_width=True)
                n_ok = jml["Baru"] + jml["Perbarui"]
                if st.button(f"Impor {n_ok} sub kegiatan", type="primary", disabled=n_ok == 0, key="ang_impor"):
                    n = terapkan_anggaran(rencana, th)
                    selesai_simpan(f"Impor {n} sub kegiatan anggaran {th} dari Excel")


if halaman == ANGGARAN_HAL:
    halaman_anggaran()
if adalah_admin() and halaman == "Pegawai":
    halaman_pegawai()
if adalah_admin() and halaman == "Bidang":
    daftar_sederhana("Bidang", "bidang", "Pengelompokan pegawai, misalnya bidang atau seksi. "
                     "Boleh dikosongkan kalau tidak diperlukan. Setelah ditambah, pilih bidang "
                     "di formulir pegawai.")
if adalah_admin() and halaman == "Sub bidang":
    halaman_subbidang()
if adalah_admin() and halaman == "Komponen data dukung":
    struktur = get_struktur()
    st.caption("Atur komponen dan isi tabel di menu Data dukung evaluasi. Setiap perubahan langsung "
               "tersimpan: ketik lalu tekan Enter (nama komponen) atau klik di luar kolom / tekan Ctrl+Enter "
               "(isi tabel). Keterangan dan link yang sudah "
               "diisi ikut terhapus kalau barisnya dihapus.")
    if st.session_state.get("pesan_isian"):
        st.error(st.session_state.pesan_isian)
    konfirm = st.session_state.get("dk_konfirm")
    for n, k in enumerate(struktur, start=1):
        sid = k["id"]
        with st.container(border=True):
            h = st.columns([6, 0.8, 0.8, 1.6], vertical_alignment="bottom")
            kw = f"dk_nama_{sid}"
            h[0].text_input(f"Komponen {n}", value=k["nama"], key=kw, on_change=cb_ds_nama, args=(sid, kw))
            h[1].button("↑", key=f"dk_ku_{sid}", on_click=cb_ds_geser_k, args=(sid, -1),
                        disabled=n == 1, help="Naikkan komponen", use_container_width=True)
            h[2].button("↓", key=f"dk_kd_{sid}", on_click=cb_ds_geser_k, args=(sid, 1),
                        disabled=n == len(struktur), help="Turunkan komponen", use_container_width=True)
            if konfirm == f"k:{sid}":
                h[3].button("Ya, hapus", key=f"dk_kh2_{sid}", type="primary", on_click=cb_ds_hapus_k,
                            args=(sid,), use_container_width=True)
            else:
                h[3].button("Hapus komponen", key=f"dk_kh_{sid}", on_click=cb_ds_konfirm,
                            args=(f"k:{sid}",), use_container_width=True)
            for i, b in enumerate(k["baris"], start=1):
                rid = b["id"]
                r = st.columns([0.4, 4.2, 3.2, 0.7, 0.7, 1.4], vertical_alignment="center")
                r[0].markdown(f"**{i}.**")
                kd, kb = f"dk_d_{sid}_{rid}", f"dk_b_{sid}_{rid}"
                r[1].text_area("Data pendukung", value=b["data"], key=kd, label_visibility="collapsed",
                               height=80, on_change=cb_ds_baris, args=(sid, rid, "data", kd))
                r[2].text_area("Bukti dukung", value=b["bukti"], key=kb, label_visibility="collapsed",
                               height=80, placeholder="Bukti dukung (boleh kosong)",
                               on_change=cb_ds_baris, args=(sid, rid, "bukti", kb))
                r[3].button("↑", key=f"dk_bu_{rid}", on_click=cb_ds_geser_b, args=(sid, rid, -1),
                            disabled=i == 1, help="Naikkan baris", use_container_width=True)
                r[4].button("↓", key=f"dk_bd_{rid}", on_click=cb_ds_geser_b, args=(sid, rid, 1),
                            disabled=i == len(k["baris"]), help="Turunkan baris", use_container_width=True)
                if konfirm == f"b:{rid}":
                    r[5].button("Ya, hapus", key=f"dk_bh2_{rid}", type="primary", on_click=cb_ds_hapus_b,
                                args=(sid, rid), use_container_width=True)
                else:
                    r[5].button("Hapus", key=f"dk_bh_{rid}", on_click=cb_ds_konfirm,
                                args=(f"b:{rid}",), use_container_width=True)
            st.button("+ Tambah data pendukung", key=f"dk_bt_{sid}", on_click=cb_ds_tambah_b, args=(sid,))
    st.button("+ Tambah komponen", key="dk_kt", type="primary", on_click=cb_ds_tambah_k)

if adalah_admin() and halaman == "Tanggal dikecualikan":
    daftar_libur()
if adalah_admin() and halaman == "Cadangan dan pindah data":
    cadangan()
