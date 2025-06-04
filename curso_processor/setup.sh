#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║                 CURSO PROCESSOR SETUP                      ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar se Python está instalado
echo -e "${YELLOW}Verificando dependências...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 não encontrado. Por favor, instale o Python 3.${NC}"
    exit 1
fi

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 não encontrado. Por favor, instale o pip3.${NC}"
    exit 1
fi

# Verificar se FFmpeg está instalado
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}FFmpeg não encontrado. Tentando instalar...${NC}"
    
    # Detectar sistema operacional
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y ffmpeg
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            sudo yum install -y ffmpeg
        elif command -v pacman &> /dev/null; then
            # Arch Linux
            sudo pacman -S ffmpeg
        else
            echo -e "${RED}Não foi possível instalar FFmpeg automaticamente. Por favor, instale manualmente.${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo -e "${RED}Homebrew não encontrado. Por favor, instale o Homebrew e depois o FFmpeg.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Sistema operacional não suportado para instalação automática de FFmpeg. Por favor, instale manualmente.${NC}"
        exit 1
    fi
fi

# Criar ambiente virtual
echo -e "${YELLOW}Criando ambiente virtual...${NC}"
python3 -m venv venv

# Ativar ambiente virtual
echo -e "${YELLOW}Ativando ambiente virtual...${NC}"
source venv/bin/activate

# Instalar dependências
echo -e "${YELLOW}Instalando dependências...${NC}"
pip install -r requirements.txt

# Criar arquivo .env a partir do exemplo
if [ ! -f .env ]; then
    echo -e "${YELLOW}Criando arquivo .env a partir do exemplo...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Arquivo .env criado. Por favor, edite-o com suas credenciais.${NC}"
fi

# Criar diretórios necessários
echo -e "${YELLOW}Criando diretórios necessários...${NC}"
mkdir -p data/{audio,transcriptions,processed,tts,xml}

# Tornar o script principal executável
echo -e "${YELLOW}Tornando o script principal executável...${NC}"
chmod +x main.py

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║             INSTALAÇÃO CONCLUÍDA COM SUCESSO!              ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Para iniciar o Curso Processor, execute:${NC}"
echo -e "${YELLOW}source venv/bin/activate && ./main.py${NC}"
echo ""
echo -e "${BLUE}Não se esqueça de configurar suas credenciais no arquivo .env${NC}"
echo ""