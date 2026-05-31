# 📥 Instagram Video Downloader Ultra

> Aplicação desktop com interface gráfica premium para download de vídeos do Instagram em máxima qualidade, com conversão automática para MP4 compatível com Windows.

---

## ✨ Sobre o projeto

O **Instagram Video Downloader Ultra** é uma ferramenta desktop feita com Python que permite baixar vídeos do Instagram de forma simples, rápida e com a melhor qualidade disponível. A interface foi construída com **CustomTkinter**, resultando num visual escuro e futurista que se diferencia das ferramentas genéricas da categoria.

O projeto usa o **yt-dlp** como motor de download e integra o **FFmpeg** para garantir que os arquivos gerados sejam totalmente compatíveis com o Windows Player e demais reprodutores, sem necessidade de codecs adicionais.

---

## 🖼️ Interface

A UI foi projetada com foco em usabilidade e estética premium:

- Tema escuro com paleta azul ciano `#68E1FD`
- Barra de progresso em tempo real
- Painel de log com timestamps
- Feedback de velocidade de download e tempo restante
- Botão de cancelamento com limpeza automática de arquivos parciais

---

## 🚀 Funcionalidades

- **Download em máxima qualidade** — prioriza MP4/H.264 + M4A diretamente, com fallback inteligente para o melhor formato disponível
- **Conversão automática com FFmpeg** — reempacota o vídeo para H.264 + AAC com flag `faststart`, garantindo compatibilidade nativa com Windows Media Player e reprodutores embarcados
- **Barra de progresso ao vivo** — exibe percentual, velocidade (MB/s) e ETA durante o download
- **Cancelamento seguro** — interrompe o download via thread e limpa arquivos `.part`, `.ytdl`, `.temp` automaticamente
- **Seleção de pasta de destino** — padrão `~/Downloads`, podendo ser alterada via explorador de arquivos
- **Validação de link** — avisa caso o link não seja do Instagram e confirma antes de prosseguir
- **Compatível com PyInstaller** — inclui suporte a `sys._MEIPASS` para empacotamento em `.exe`
- **Retentativas automáticas** — 5 tentativas por segmento em caso de falha de rede

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Papel no projeto |
|---|---|
| Python 3.x | Linguagem principal |
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Interface gráfica moderna |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Motor de download |
| FFmpeg | Pós-processamento e conversão de vídeo |
| threading | Download assíncrono sem travar a UI |
| queue.Queue | Comunicação thread-safe entre worker e UI |

---

## 📦 Instalação

### Pré-requisitos

- Python 3.9 ou superior
- [FFmpeg](https://ffmpeg.org/download.html) instalado e no PATH (recomendado)

### Passos

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/insta-downloader-premium.git
cd insta-downloader-premium

# Instale as dependências
pip install customtkinter yt-dlp

# Execute a aplicação
python insta_downloader_premium.py
```

> **Nota:** O FFmpeg não é obrigatório para rodar, mas é altamente recomendado. Sem ele, o download pode funcionar parcialmente, mas a conversão e compatibilidade do MP4 ficam limitadas.

---

## 🔧 Como usar

1. Cole o link do vídeo do Instagram no campo **"Link do vídeo"**
2. Escolha a pasta de destino (padrão: `Downloads`)
3. Clique em **⬇ BAIXAR EM QUALIDADE MÁXIMA**
4. Acompanhe o progresso na barra e no painel de log
5. Ao concluir, uma janela confirma o caminho do arquivo salvo

Para cancelar um download em andamento, clique em **Cancelar download** — os arquivos parciais são removidos automaticamente.

---

## ⚙️ Detalhes técnicos

### Seleção de formato

O app usa uma cadeia de prioridades para garantir o melhor vídeo possível:

```
bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]
  → best[ext=mp4][vcodec^=avc1]
  → bestvideo[ext=mp4]+bestaudio[ext=m4a]
  → best[ext=mp4]
  → best
```

### Pós-processamento com FFmpeg

Quando o FFmpeg está disponível, o arquivo final é recodificado com:

```
ffmpeg -c:v libx264 -preset veryfast -crf 20 -c:a aac -b:a 192k -movflags +faststart
```

Isso garante compatibilidade máxima com reprodutores nativos do Windows.

### Arquitetura de threads

O download roda em uma `Thread` daemon separada, enquanto a UI continua responsiva. A comunicação entre o worker e a interface é feita exclusivamente via `queue.Queue`, evitando condições de corrida. O método `_process_events()` é chamado a cada 150ms via `after()` do Tkinter.

---

## 📁 Estrutura do projeto

```
insta-downloader-premium/
├── insta_downloader_premium.py   # Código-fonte principal
└── README.md
```

---

## ⚠️ Limitações conhecidas

- Vídeos privados ou que exigem login não são suportados
- O Instagram pode aplicar bloqueios temporários em IPs com muitas requisições
- Reels com restrição geográfica podem falhar dependendo da região

---

## 📄 Licença

Este projeto é de uso pessoal e educacional. O uso do yt-dlp para baixar conteúdo do Instagram deve respeitar os [Termos de Uso da plataforma](https://help.instagram.com/581066165581870).

---

Feito com 🐍 Python e CustomTkinter.
---

## 🔒 Aviso Legal

Este projeto foi desenvolvido para fins educacionais e de portfólio. Utilize apenas para baixar conteúdos que você tem autorização para baixar, respeitando os os direitos autorais dos criadores.

---

## 👨‍💻 Autor

Feito com 💙 por **[Eduardo Moura Sekeff](https://github.com/eduardosekeffadv-eng)**

---

*Sinta-se à vontade para abrir uma issue ou enviar um pull request com sugestões de melhoria!*
