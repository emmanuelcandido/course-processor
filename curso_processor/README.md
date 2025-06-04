# 🎓 Curso Processor

Sistema completo para processamento automatizado de cursos em vídeo com interface CLI usando Rich + Typer seguindo o padrão Nord Theme.

## ✨ Funcionalidades

- 🎬 **Conversão de vídeo para áudio** (MP3 128kbps)
- 📝 **Transcrição automática** (Whisper API/Local)
- 🤖 **Processamento com IA** (Claude/ChatGPT)
- ⏱️ **Geração de timestamps** automática
- 🎙️ **Síntese de voz** (Edge-TTS)
- 📊 **Feed de podcast** (XML RSS)
- ☁️ **Upload Google Drive** automático
- 🔗 **Integração GitHub** para publicação
- 🔄 **Processamento completo** de cursos
- ⚙️ **Configurações** personalizáveis
- 📝 **Sistema de gerenciamento de prompts**

## 🚀 Instalação Rápida

```bash
git clone https://github.com/seu-usuario/curso-processor
cd curso-processor
pip install -r requirements.txt
python main.py
```

## ⚙️ Configuração Inicial

1. **APIs necessárias:**
   - OpenAI API Key
   - Anthropic API Key  
   - Google Drive Service Account
   - GitHub Token (opcional)

2. **Dependências do sistema:**
   ```bash
   # Para Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y ffmpeg

   # Para macOS
   brew install ffmpeg

   # Para Windows
   # Baixe e instale o FFmpeg de https://ffmpeg.org/download.html
   ```

3. **Permissões de execução:**
   ```bash
   chmod +x main.py
   ```

## 🖥️ Uso

Execute o script principal:
```bash
./main.py
```

Ou:
```bash
python main.py
```

## 📝 Sistema de Gerenciamento de Prompts

O Sistema de Gerenciamento de Prompts permite:

1. Criar, editar e gerenciar prompts de IA para diferentes tipos de conteúdo
2. Testar a eficácia dos prompts com transcrições de exemplo
3. Acompanhar estatísticas de uso dos prompts
4. Gerenciar versões de prompts com versionamento automático
5. Exportar e importar prompts entre instalações
6. Usar prompts especializados para diferentes tipos de conteúdo

### Usando o Gerenciador de Prompts

```bash
# Execute o gerenciador de prompts standalone
python prompt_manager_standalone.py

# Ou acesse pelo menu principal (opção 12)
python main.py
```

### Templates de Prompts Disponíveis

- **default_prompt.txt**: Template principal para conteúdo geral
- **technical_prompt.txt**: Especializado para conteúdo técnico
- **summary_prompt.txt**: Para resumos executivos
- **business_content.txt**: Para conteúdo de negócios
- **quick_summary.txt**: Para resumos rápidos
- **detailed_analysis.txt**: Para análises detalhadas

### Templates de Prompts Personalizados

- **marketing_specialist.txt**: Para documentos de estratégia de marketing
- **programming_tutor.txt**: Para tutoriais de programação
- **data_analyst.txt**: Para relatórios de análise de dados
- **educational_curriculum.txt**: Para design de currículos educacionais

## 📊 Gerador de XML para Podcast

O módulo Gerador de XML para Podcast permite:

1. Criar feeds RSS para podcast
2. Adicionar episódios de cursos aos feeds
3. Atualizar feeds existentes
4. Validar feeds XML
5. Gerar timestamps a partir de arquivos de áudio

### Criando um Feed de Podcast

```python
from modules import xml_generator
from rich.console import Console

console = Console()

success, result = xml_generator.create_podcast_feed(
    title="Meu Feed de Podcast",
    description="Este é meu feed de podcast",
    language="pt-BR",
    category="Educação",
    author="Seu Nome",
    email="seu@email.com",
    image_url="https://exemplo.com/imagem.jpg",
    output_path="/caminho/para/feed.xml",
    console=console
)

if success:
    print(f"Feed criado com sucesso: {result}")
else:
    print(f"Falha ao criar feed: {result}")
```

### Adicionando um Curso ao Feed

```python
success, result = xml_generator.add_course_to_feed(
    xml_path="/caminho/para/feed.xml",
    course_name="Meu Curso",
    audio_url="https://exemplo.com/curso.mp3",
    timestamps_path="/caminho/para/timestamps.md",
    duration="01:30:00",
    author="Seu Nome",
    console=console
)

if success:
    print(f"Curso adicionado com sucesso: {result}")
else:
    print(f"Falha ao adicionar curso: {result}")
```

## 🐳 Suporte a Docker

O Curso Processor pode ser executado em um contêiner Docker para facilitar a implantação e evitar problemas de dependência.

### Construindo a Imagem Docker

```bash
# Construa a imagem Docker
docker build -t curso-processor .

# Execute o contêiner
docker run -it --name curso-processor-app curso-processor
```

### Usando Docker Compose

```yaml
# docker-compose.yml
version: '3'
services:
  curso-processor:
    build: .
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

## 📄 Licença

MIT