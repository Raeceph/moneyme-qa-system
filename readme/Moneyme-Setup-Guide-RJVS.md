#MoneyMe QA System Setup Guide

## Prerequisites
- Docker and Docker Compose installed on your system
- Git installed on your system
- Basic knowledge of terminal/command line operations

## Setup Steps

1. **Clone the GitHub Repository**
   ```bash
   git clone https://github.com/Raeceph/moneyme-qa-system.git
   cd moneyme-qa-system
   ```

2. **Prepare PDF Directory**
   ```bash
   mkdir -p ~/Documents/pdfs
   # Move your PDFs to this directory
   mv /path/to/your/pdfs/*.pdf ~/Documents/pdfs/
   ```

3. **Ensure Configuration Files**
   Verify that the following files exist in your project root with the correct content:
   - `docker-compose.yml`
   - `Dockerfile`
   - `entrypoint.sh`

4. **Build and Start Services**
   Ensure you are in the project directory, then run:
   ```bash
   docker-compose up -d --build
   ```

5. **Download Mistral Model**
   ```bash
   docker-compose exec ollama ollama pull mistral
   ```

6. **Verify Mistral Model**
   ```bash
   docker-compose exec ollama ollama list
   ```
   You should see 'mistral' in the list of available models.

Your MoneyMe QA System is now set up and ready to use!

