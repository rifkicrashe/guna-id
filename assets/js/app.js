"use strict";

const formatRupiah = n => "Rp " + Number(n).toLocaleString("id-ID", {
  maximumFractionDigits: 2
});

function calculate(type, form) {
  const field = name => form.querySelector(`[name="${name}"]`);
  const raw = name => field(name)?.value ?? "";
  const num = name => Number(raw(name) || 0);
  const a = num("a"), b = num("b"), c = num("c");
  const text = raw("text");

  switch (type) {
    case "discount":
      if (b < 0 || b > 100) return "Diskon harus 0–100%.";
      return formatRupiah(a * (1 - b / 100));
    case "installment":
      return b > 0 ? formatRupiah(a / b) + " per bulan (tanpa bunga)" : "Jumlah bulan harus lebih dari 0.";
    case "interest":
      return formatRupiah(a * b / 100);
    case "profit":
    case "daily":
      return formatRupiah(a - b);
    case "margin":
      return a > 0 ? ((a - b) / a * 100).toFixed(2) + "%" : "Harga jual harus lebih dari 0.";
    case "bep":
      return b > c ? Math.ceil(a / (b - c)) + " unit" : "Harga jual harus lebih besar dari biaya variabel.";
    case "percentage":
      return formatRupiah(a * b / 100);
    case "selling":
      return b >= 100 || b < 0 ? "Margin harus 0–99,99%." : formatRupiah(a / (1 - b / 100));
    case "capital":
      return formatRupiah(a + b + c);
    case "stock":
      return a + b - c + " unit";
    case "salary":
      return formatRupiah(a - b);
    case "overtime":
      return formatRupiah(a * b * 1.5) + " (estimasi 1,5x)";
    case "thr":
      return formatRupiah(b >= 12 ? a : a * Math.max(0, b) / 12);
    case "worktime": {
      if (a < 0 || a > 24 || b < 0 || b > 24) return "Jam harus antara 0 dan 24.";
      const duration = b >= a ? b - a : 24 - a + b;
      return duration.toFixed(2) + " jam";
    }
    case "fuel":
    case "travel":
    case "electricity":
      return formatRupiah(a * b);
    case "consumption":
      return b > 0 ? (a / b).toFixed(2) + " km/liter" : "Liter BBM harus lebih dari 0.";
    case "age": {
      const value = raw("a");
      const birth = new Date(value + "T00:00:00");
      if (!value || Number.isNaN(birth.getTime()) || birth > new Date()) return "Tanggal lahir tidak valid.";
      const now = new Date();
      let age = now.getFullYear() - birth.getFullYear();
      if (now.getMonth() < birth.getMonth() ||
          (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())) age--;
      return age + " tahun";
    }
    case "words":
      return (text.trim() ? text.trim().split(/\s+/u).length : 0) + " kata";
    case "characters":
      return [...text].length + " karakter";
    case "textcase": {
      const mode = raw("mode");
      if (mode === "upper") return text.toUpperCase();
      if (mode === "lower") return text.toLowerCase();
      return text.toLowerCase().replace(/\b\p{L}/gu, x => x.toUpperCase());
    }
    case "json":
      try { return JSON.stringify(JSON.parse(text), null, 2); }
      catch { return "JSON tidak valid."; }
    case "password": {
      const len = Math.max(8, Math.min(128, Math.floor(a || 16)));
      const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*";
      const bytes = new Uint8Array(len);
      crypto.getRandomValues(bytes);
      return Array.from(bytes, x => chars[x % chars.length]).join("");
    }
    case "invoice":
    case "receipt":
      return "Dokumen: " + text + "\nNominal: " + formatRupiah(a) +
        "\nGunakan fitur cetak browser untuk menyimpan sebagai PDF.";
    case "qr":
      return "QR Generator belum aktif.";
    default:
      return "Jenis alat belum didukung.";
  }
}

let qrLibraryLoading = null;

function loadQrLibrary() {
  if (window.QRCode) return Promise.resolve();
  if (qrLibraryLoading) return qrLibraryLoading;

  qrLibraryLoading = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js";
    script.onload = resolve;
    script.onerror = () => {
      qrLibraryLoading = null;
      reject(new Error("Library QR gagal dimuat. Periksa koneksi internet."));
    };
    document.head.appendChild(script);
  });

  return qrLibraryLoading;
}

async function generateQr(form, result) {
  const text = form.querySelector('[name="text"]')?.value.trim() || "";
  result.replaceChildren();

  if (!text) {
    result.textContent = "Masukkan teks atau URL terlebih dahulu.";
    return;
  }

  result.textContent = "Membuat QR Code...";

  try {
    await loadQrLibrary();
    result.replaceChildren();

    const preview = document.createElement("div");
    preview.style.cssText = "display:flex;justify-content:center;background:#fff;padding:16px;margin:12px auto;width:max-content;max-width:100%;";

    const mount = document.createElement("div");
    preview.appendChild(mount);
    result.appendChild(preview);

    new QRCode(mount, {
      text,
      width: 256,
      height: 256,
      colorDark: "#000000",
      colorLight: "#ffffff",
      correctLevel: QRCode.CorrectLevel.H
    });

    const download = document.createElement("button");
    download.type = "button";
    download.textContent = "Unduh QR sebagai PNG";
    download.style.marginTop = "12px";

    download.addEventListener("click", () => {
      const source = mount.querySelector("canvas") || mount.querySelector("img");

      if (!source) {
        alert("QR belum siap. Coba lagi.");
        return;
      }

      const width = source instanceof HTMLCanvasElement
        ? source.width : source.naturalWidth;
      const height = source instanceof HTMLCanvasElement
        ? source.height : source.naturalHeight;

      if (!width || !height) {
        alert("QR belum siap. Coba lagi.");
        return;
      }

      const padding = 32;
      const output = document.createElement("canvas");
      output.width = width + padding * 2;
      output.height = height + padding * 2;

      const ctx = output.getContext("2d");
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, output.width, output.height);
      ctx.drawImage(source, padding, padding, width, height);

      const url = output.toDataURL("image/png");
      const link = document.createElement("a");
      link.href = url;
      link.download = "guna-id-qr.png";
      document.body.appendChild(link);
      link.click();
      link.remove();
    });

    result.appendChild(download);
  } catch (error) {
    result.textContent = error.message || "QR gagal dibuat.";
  }
}

document.querySelectorAll(".tool-form").forEach(form => {
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const result = form.closest(".tool-panel-body")?.querySelector(".result");
    if (!result) return;

    if (form.dataset.type === "qr") {
      await generateQr(form, result);
      return;
    }

    result.textContent = calculate(form.dataset.type, form);
  });
});
