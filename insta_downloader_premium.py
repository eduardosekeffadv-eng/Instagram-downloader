import os
import re
import sys
import glob
import queue
import shutil
import threading
import subprocess
from pathlib import Path
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, messagebox

import yt_dlp


APP_NAME = "Instagram Video Downloader Ultra"
APP_VERSION = "1.0"


class CancelDownload(Exception):
    """Exceção interna usada para cancelar o download com segurança."""
    pass


def resource_path(relative_path: str) -> str:
    """
    Ajuda quando o programa virar .exe com PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def clean_filename(name: str) -> str:
    """
    Remove caracteres problemáticos para nome de arquivo no Windows.
    """
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:120] if name else "video_instagram"


def has_ffmpeg() -> bool:
    """
    Verifica se o FFmpeg está disponível no PATH.
    Ele é importante para garantir MP4 compatível com Windows.
    """
    return shutil.which("ffmpeg") is not None


class InstagramDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("920x620")
        self.minsize(840, 560)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.download_thread = None
        self.cancel_requested = False
        self.current_output_path = None
        self.events = queue.Queue()

        self._build_ui()
        self._process_events()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self, corner_radius=28, fg_color=("#101624", "#080D16"))
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=22, pady=22)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="INSTAGRAM DOWNLOADER",
            font=ctk.CTkFont(family="Segoe UI", size=34, weight="bold"),
            text_color="#68E1FD"
        )
        self.title_label.grid(row=0, column=0, pady=(28, 4), padx=28, sticky="ew")

        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Baixe vídeos em MP4, na melhor qualidade disponível, com interface premium futurista.",
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color="#AAB7CF"
        )
        self.subtitle_label.grid(row=1, column=0, pady=(0, 22), padx=28, sticky="ew")

        self.card = ctk.CTkFrame(self.main_frame, corner_radius=24, fg_color="#111A2E", border_width=1, border_color="#1E8DF7")
        self.card.grid(row=2, column=0, padx=34, pady=14, sticky="ew")
        self.card.grid_columnconfigure(1, weight=1)

        self.url_label = ctk.CTkLabel(
            self.card,
            text="Link do vídeo",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#EAF6FF"
        )
        self.url_label.grid(row=0, column=0, padx=(26, 14), pady=(26, 8), sticky="w")

        self.url_entry = ctk.CTkEntry(
            self.card,
            height=44,
            corner_radius=14,
            border_color="#2E9BFF",
            placeholder_text="Cole aqui o link do Instagram...",
            font=ctk.CTkFont(size=14)
        )
        self.url_entry.grid(row=0, column=1, padx=(0, 26), pady=(26, 8), sticky="ew")

        self.folder_label = ctk.CTkLabel(
            self.card,
            text="Salvar em",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#EAF6FF"
        )
        self.folder_label.grid(row=1, column=0, padx=(26, 14), pady=8, sticky="w")

        default_folder = str(Path.home() / "Downloads")
        self.folder_var = ctk.StringVar(value=default_folder)

        self.folder_entry = ctk.CTkEntry(
            self.card,
            textvariable=self.folder_var,
            height=44,
            corner_radius=14,
            border_color="#2E9BFF",
            font=ctk.CTkFont(size=14)
        )
        self.folder_entry.grid(row=1, column=1, padx=(0, 12), pady=8, sticky="ew")

        self.choose_button = ctk.CTkButton(
            self.card,
            text="Escolher pasta",
            height=44,
            corner_radius=14,
            fg_color="#263B63",
            hover_color="#315182",
            command=self.choose_folder
        )
        self.choose_button.grid(row=1, column=2, padx=(0, 26), pady=8, sticky="e")

        self.progress = ctk.CTkProgressBar(
            self.card,
            height=16,
            corner_radius=12,
            progress_color="#68E1FD"
        )
        self.progress.grid(row=2, column=0, columnspan=3, padx=26, pady=(24, 8), sticky="ew")
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            self.card,
            text="Pronto para baixar.",
            font=ctk.CTkFont(size=14),
            text_color="#AAB7CF"
        )
        self.status_label.grid(row=3, column=0, columnspan=3, padx=26, pady=(4, 22), sticky="w")

        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buttons_frame.grid(row=3, column=0, padx=34, pady=(18, 8), sticky="ew")
        self.buttons_frame.grid_columnconfigure((0, 1), weight=1)

        self.download_button = ctk.CTkButton(
            self.buttons_frame,
            text="⬇ BAIXAR EM QUALIDADE MÁXIMA",
            height=56,
            corner_radius=18,
            fg_color="#00A7FF",
            hover_color="#0078D7",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_download
        )
        self.download_button.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.cancel_button = ctk.CTkButton(
            self.buttons_frame,
            text="Cancelar download",
            height=56,
            corner_radius=18,
            fg_color="#3B4254",
            hover_color="#D93636",
            state="disabled",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.cancel_download
        )
        self.cancel_button.grid(row=0, column=1, padx=(10, 0), sticky="ew")

        self.log_box = ctk.CTkTextbox(
            self.main_frame,
            height=155,
            corner_radius=20,
            fg_color="#060A12",
            border_width=1,
            border_color="#20314F",
            text_color="#C7D8FF",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.log_box.grid(row=4, column=0, padx=34, pady=(16, 24), sticky="nsew")
        self.main_frame.grid_rowconfigure(4, weight=1)

        self._log("Sistema iniciado.")
        self._log("Cole o link, escolha a pasta e clique em baixar.")
        if not has_ffmpeg():
            self._log("Aviso: FFmpeg não encontrado. O download pode funcionar, mas a conversão/compatibilidade MP4 pode ficar limitada.")

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def start_download(self):
        url = self.url_entry.get().strip()
        folder = self.folder_var.get().strip()

        if not url:
            messagebox.showwarning("Atenção", "Cole o link do vídeo do Instagram antes de baixar.")
            return

        if "instagram.com" not in url.lower():
            proceed = messagebox.askyesno(
                "Confirmar link",
                "Esse link não parece ser do Instagram. Deseja tentar mesmo assim?"
            )
            if not proceed:
                return

        if not folder:
            messagebox.showwarning("Atenção", "Escolha uma pasta para salvar o vídeo.")
            return

        Path(folder).mkdir(parents=True, exist_ok=True)

        self.cancel_requested = False
        self.progress.set(0)
        self.status_label.configure(text="Preparando download...")
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.url_entry.configure(state="disabled")
        self.choose_button.configure(state="disabled")
        self.folder_entry.configure(state="disabled")

        self._log("Iniciando download...")
        self.download_thread = threading.Thread(
            target=self._download_worker,
            args=(url, folder),
            daemon=True
        )
        self.download_thread.start()

    def cancel_download(self):
        self.cancel_requested = True
        self.cancel_button.configure(state="disabled")
        self.status_label.configure(text="Cancelando download...")
        self._log("Cancelamento solicitado pelo usuário.")

    def _progress_hook(self, data):
        if self.cancel_requested:
            raise CancelDownload("Download cancelado pelo usuário.")

        status = data.get("status")

        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes", 0)

            if total:
                percent = max(0, min(downloaded / total, 1))
                self.events.put(("progress", percent))

            speed = data.get("speed")
            eta = data.get("eta")

            speed_text = self._format_speed(speed)
            eta_text = self._format_eta(eta)
            self.events.put(("status", f"Baixando... {speed_text} | Tempo restante: {eta_text}"))

        elif status == "finished":
            filename = data.get("filename")
            self.current_output_path = filename
            self.events.put(("progress", 0.95))
            self.events.put(("status", "Download concluído. Finalizando arquivo MP4..."))

    @staticmethod
    def _format_speed(speed):
        if not speed:
            return "velocidade calculando"
        mb = speed / 1024 / 1024
        return f"{mb:.2f} MB/s"

    @staticmethod
    def _format_eta(eta):
        if eta is None:
            return "calculando"
        minutes, seconds = divmod(int(eta), 60)
        if minutes:
            return f"{minutes}min {seconds}s"
        return f"{seconds}s"

    def _download_worker(self, url: str, folder: str):
        try:
            date_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_template = str(Path(folder) / f"%(title).120s_{date_tag}.%(ext)s")

            ydl_opts = {
                # Melhor qualidade dando preferência a MP4/H.264/M4A quando disponível.
                "format": (
                    "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/"
                    "best[ext=mp4][vcodec^=avc1]/"
                    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
                    "best[ext=mp4]/best"
                ),
                "format_sort": ["res", "fps", "codec:avc:m4a", "size", "br"],
                "merge_output_format": "mp4",
                "outtmpl": output_template,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [self._progress_hook],
                "windowsfilenames": True,
                "retries": 5,
                "fragment_retries": 5,
                "continuedl": True,
            }

            if has_ffmpeg():
                ydl_opts["postprocessors"] = [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4",
                    }
                ]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            final_path = self._find_final_file(folder, info, date_tag)

            if final_path and has_ffmpeg():
                compatible_path = self._ensure_windows_mp4(final_path)
                final_path = compatible_path or final_path

            self.events.put(("progress", 1.0))
            self.events.put(("status", "Download finalizado com sucesso."))
            self.events.put(("done", final_path))

        except CancelDownload:
            self._cleanup_partial_files(folder)
            self.events.put(("cancelled", None))

        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _find_final_file(self, folder: str, info: dict, date_tag: str):
        """
        Tenta localizar o arquivo final baixado.
        """
        candidates = sorted(
            Path(folder).glob(f"*_{date_tag}.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        candidates = [
            p for p in candidates
            if p.suffix.lower() in [".mp4", ".mkv", ".webm", ".mov"]
            and not str(p).endswith(".part")
        ]

        if candidates:
            return str(candidates[0])

        requested = info.get("requested_downloads") if isinstance(info, dict) else None
        if requested:
            filepath = requested[0].get("filepath")
            if filepath and Path(filepath).exists():
                return filepath

        return None

    def _ensure_windows_mp4(self, input_path: str):
        """
        Reempacota/converte para MP4 com H.264 + AAC quando necessário.
        Isso aumenta a chance de abrir normalmente no Windows.
        """
        input_file = Path(input_path)

        if not input_file.exists():
            return None

        if input_file.suffix.lower() != ".mp4":
            output_file = input_file.with_suffix(".mp4")
        else:
            output_file = input_file.with_name(input_file.stem + "_windows.mp4")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_file),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_file)
        ]

        self.events.put(("status", "Otimizando MP4 para reprodução no Windows..."))

        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if result.returncode == 0 and output_file.exists():
            try:
                if input_file != output_file and input_file.exists():
                    input_file.unlink()
            except Exception:
                pass
            return str(output_file)

        return str(input_file)

    def _cleanup_partial_files(self, folder: str):
        patterns = ["*.part", "*.ytdl", "*.temp", "*.tmp"]
        for pattern in patterns:
            for file in glob.glob(str(Path(folder) / pattern)):
                try:
                    os.remove(file)
                except Exception:
                    pass

    def _process_events(self):
        try:
            while True:
                event, value = self.events.get_nowait()

                if event == "progress":
                    self.progress.set(value)

                elif event == "status":
                    self.status_label.configure(text=value)
                    self._log(value)

                elif event == "done":
                    self._reset_buttons()
                    if value:
                        self._log(f"Arquivo salvo em: {value}")
                        messagebox.showinfo("Concluído", f"Download finalizado com sucesso!\n\nArquivo:\n{value}")
                    else:
                        messagebox.showinfo("Concluído", "Download finalizado, mas não consegui identificar o caminho do arquivo.")

                elif event == "cancelled":
                    self.progress.set(0)
                    self.status_label.configure(text="Download cancelado.")
                    self._log("Download cancelado com sucesso.")
                    self._reset_buttons()

                elif event == "error":
                    self.progress.set(0)
                    self.status_label.configure(text="Erro no download.")
                    self._log(f"Erro: {value}")
                    self._reset_buttons()
                    messagebox.showerror(
                        "Erro",
                        "Não foi possível baixar esse vídeo.\n\n"
                        "Possíveis causas:\n"
                        "- vídeo privado;\n"
                        "- link exige login;\n"
                        "- bloqueio temporário do Instagram;\n"
                        "- FFmpeg ausente;\n"
                        "- link inválido.\n\n"
                        f"Detalhe técnico:\n{value}"
                    )

        except queue.Empty:
            pass

        self.after(150, self._process_events)

    def _reset_buttons(self):
        self.download_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.url_entry.configure(state="normal")
        self.choose_button.configure(state="normal")
        self.folder_entry.configure(state="normal")

    def _log(self, text: str):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{now}] {text}\n")
        self.log_box.see("end")


if __name__ == "__main__":
    app = InstagramDownloaderApp()
    app.mainloop()
