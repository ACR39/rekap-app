# Rekap Isian Pekerja (Streamlit)

Mencatat siapa yang sudah mengisi laporan pada hari Jumat (WFA) dan menampilkan
siapa yang belum, per nama beserta tanggalnya. Tanggal merah bisa dikecualikan.

## Cara memasang

1. **Buat dua repositori privat di GitHub**
   - `rekap-app`: berisi `app.py` dan `requirements.txt` dari folder ini.
   - `rekap-data`: repositori kosong khusus data. Dipisah supaya setiap
     penyimpanan data tidak membuat aplikasi dimulai ulang.
     Buat satu file apa saja (misalnya README) agar branch `main` ada.
2. **Buat token GitHub**: Settings > Developer settings > Personal access
   tokens > Fine-grained tokens. Pilih hanya repositori `rekap-data`, izin
   *Contents: Read and write*.
3. **Deploy di Streamlit Community Cloud** (share.streamlit.io): pilih repositori
   `rekap-app`, file utama `app.py`.
4. **Isi Secrets** di App settings > Secrets, ikuti
   `.streamlit/secrets.toml.example`. Jangan taruh token di kode.
5. Buka aplikasinya, mulai dari tab **Kelola** untuk menambah pekerja.

## Catatan

- Tanpa pengaturan `[github]`, aplikasi memakai file lokal `data.json`. Itu hanya
  untuk uji coba, karena file lokal di Streamlit Cloud bisa hilang saat restart.
- Setiap simpan menjadi satu commit di `rekap-data`, jadi riwayat perubahan
  bisa dilihat di GitHub.
- Kalau dua orang menyimpan bersamaan, yang kedua mendapat pemberitahuan dan
  data terbaru dimuat otomatis. Perubahannya perlu diulang.
- Hanya hari Jumat yang dihitung. Batas rentang laporan 2 tahun.
- Menjalankan di komputer sendiri: `pip install -r requirements.txt` lalu
  `streamlit run app.py`.
