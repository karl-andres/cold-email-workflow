from src.memory.semantic import append_fact
import asyncio
from src.db import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        # Identity
        await append_fact(db, "karl", "- 2nd year Software Engineering student at McMaster University (GPA: 3.9, Expected Graduation: May 2028)")

        # Internship — Wizonix
        await append_fact(db, "karl", "- Software Engineer Intern at Wizonix (Feb–Mar 2026): built a RAG pipeline in Python + Neo4j, improving retrieval speed by 54% and accuracy by 33% over baseline APIs")
        await append_fact(db, "karl", "- Built an MCP server connecting to LangChain agents for automated document ingestion and semantic querying, with tool filtering to block prompt injection attacks")
        await append_fact(db, "karl", "- Engineered an OCR pipeline using Tesseract + Azure-hosted Mistral OCR as fallback, achieving 99%+ extraction confidence with instant semantic search for users")
        await append_fact(db, "karl", "- Integrated third-party logistics platforms via REST APIs (FastAPI) and webhooks for a live Transportation Management System (TMS)")

        # McMaster EcoCAR
        await append_fact(db, "karl", "- Software Developer on McMaster EcoCAR Autonomous Vehicle Team (Sep 2025–Present): replaced road resistance feedforward algorithm using Python + pandas, improving ACC reliability by 23%")
        await append_fact(db, "karl", "- Debugged GitLab CI pipeline failures and corrected mismatched signal names, improving automated test reliability and telemetry data integrity")
        await append_fact(db, "karl", "- Built a Python data analysis pipeline that validated 3+ critical technical specs from CAN logs and auto-formatted results for submission")

        # Project — fl-studio-mcp
        await append_fact(db, "karl", "- fl-studio-mcp: Python MCP server exposing 50+ DAW automation tools to LLMs, with a MIDI/JSON communication bridge to bypass API limitations; cross-platform Bash setup script reduced setup time by 90%")

        # Project — GitCheck
        await append_fact(db, "karl", "- GitCheck (Turnitin for Hackathons): LangChain + LangGraph agent workflow that validates Devpost submissions against their codebase; org-based access with Auth0 for data isolation")

        # Project — GenAI Audio Platform (ModelSense)
        await append_fact(db, "karl", "- Fullstack GenAI Audio Platform: text-to-music platform with Next.js + Tailwind frontend, FastAPI backend, Inngest for async task orchestration, PostgreSQL metadata, AWS S3 storage — scaled to 1,000+ test tracks")

        # Project — NexHacks CMU '26
        await append_fact(db, "karl", "- NexHacks CMU '26: GenAI platform in TypeScript + Python converting camera data into 3D STL meshes via CV pipelines; integrated TRELLIS AI; Docker volume caching reduced GPU cold-start latency by 90%")

        # Technical skills
        await append_fact(db, "karl", "- Languages: Java, Python, TypeScript, HTML5/CSS, SQL, C, C++, Bash")
        await append_fact(db, "karl", "- Tools/Frameworks: AWS, PostgreSQL, Git, React, Next.js, Node.js, Express, FastAPI, LangChain, LangGraph, FastMCP, Neo4j, Docker")
        await append_fact(db, "karl", "- Practices: OOP, SOLID, RESTful API Design, Agile/Scrum, RAG pipelines, agentic AI workflows, CI/CD (GitLab)")

asyncio.run(main())