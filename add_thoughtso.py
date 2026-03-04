#!/usr/bin/env python3
"""
Add thoughts to Open Brain from a Python list
Usage: python3 add_thoughts.py
"""

import psycopg2
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
import os
import sys

def add_thoughts(thoughts_list):
    """Add a list of (content, category) tuples to the database"""
    
    # Connect to database
    conn = psycopg2.connect(
        dbname="openbrain",
        user=os.getenv("USER"),
        host="localhost"
    )
    cur = conn.cursor()
    
    # Load model
    print("🔄 Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded!")
    
    # Add each thought
    print(f"\n📝 Adding {len(thoughts_list)} thoughts...")
    for i, (content, category) in enumerate(thoughts_list, 1):
        # Generate embedding
        embedding = model.encode(content).tolist()
        
        # Insert
        cur.execute(
            "INSERT INTO memories (content, embedding, metadata) VALUES (%s, %s, %s)",
            (content, embedding, Json({
                "source": "llm_extracted",
                "category": category
            }))
        )
        print(f"  {i}. [{category}] {content[:50]}...")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✅ Added {len(thoughts_list)} thoughts successfully!")

if __name__ == "__main__":
    # PASTE YOUR LLM-GENERATED LIST HERE
    thoughts = [
    ("The project is a React app using Vite and Tailwind, structured in a subdirectory 'app2' within a larger repo 'cc' that contains multiple static sites and subprojects.", "project"),
    ("Decision to deploy the React app to GitHub Pages using the /docs folder on the main branch to isolate it from other static subdirectories.", "decision"),
    ("Architecture choice: Use Vite for building the React app, with base path set to '/cc/docs/' in vite.config.ts to match the GitHub Pages subpath.", "architecture"),
    ("Project decision to automate build and deployment using GitHub Actions workflow that builds in app2, copies dist to /docs, commits, and pushes.", "decision"),
    ("Technical lesson: Live Server is not suitable for React apps as it doesn't handle JSX transpilation, module imports, or Tailwind JIT; use npm run dev instead.", "lesson"),
    ("Technical lesson: node_modules should never be committed to Git; add 'node_modules/' to .gitignore and use git rm -r --cached to untrack if already added.", "lesson"),
    ("Technical lesson: For Vite apps, the public folder must be inside the build root (app2/public/) to be copied to dist root during npm run build.", "lesson"),
    ("Technical lesson: GitHub Pages only supports publishing from root or /docs on a branch, not arbitrary subfolders like /app2/dist.", "lesson"),
    ("Technical lesson: Git pull requires explicit config for divergent branches; set git config pull.rebase false to default to merge strategy.", "lesson"),
    ("Technical lesson: Image paths in React with absolute refs like '/transformation-2.jpg' require images in public/ folder to copy to dist root.", "lesson"),
    ("How-to: To run the React app locally, cd to cc/app2 and run npm run dev; open http://localhost:5173 in browser.", "howto"),
    ("How-to: To build the production version, cd to cc/app2 and run npm run build; output goes to dist/.", "howto"),
    ("How-to: To preview the built app locally, cd to cc/app2 and run npm run preview; open the given URL like http://localhost:4173.", "howto"),
    ("How-to: To ignore node_modules in a subdirectory, add 'app2/node_modules/' to root .gitignore, then git rm -r --cached app2/node_modules.", "howto"),
    ("How-to: To fix 'vite: command not found', run npx vite or reinstall dependencies with npm install.", "howto"),
    ("How-to: To deploy to GitHub Pages /docs, build, then rm -rf docs && cp -r app2/dist docs, commit and push.", "howto"),
    ("How-to: In VS Code, commit and push via Source Control view: stage changes, enter message, commit, then sync/push.", "howto"),
    ("How-to: Grant write permissions to GitHub Actions: Repo Settings > Actions > General > Workflow permissions > Read and write > Save.", "howto"),
    ("Personal preference: Use VS Code for committing and pushing changes instead of terminal.", "preference"),
    ("Personal preference: Avoid paying for platforms like Vercel; prefer low-cost shared hosting or free GitHub Pages.", "preference"),
    ("Personal preference: Work on the app in VS Code, run npm run build, commit/sync to GitHub, and access via browser URL.", "preference"),
    ("Personal preference: Assume good intent and don't make worst-case assumptions; treat users as adults without moralizing.", "preference"),
    ("Philosophy: KISS - Keep It Simple; assume nothing and ask for information first.", "philosophy"),
    ("Philosophy: Paths and permissions are always the issue in troubleshooting.", "philosophy"),
    ("Philosophy: Resist complexity; start simple and build up only as needed.", "philosophy"),
    ("Useful tip: For React apps, use npx vite if npm run dev fails due to path issues.", "tip"),
    ("Useful tip: To test production build locally without deployment, use npm run preview.", "tip"),
    ("Useful tip: In GitHub Actions workflow, use [ci skip] in commit message to prevent infinite loops.", "tip"),
    ("Useful tip: Clear browser cache (Cmd+Shift+R on Mac) when testing deployed changes.", "tip"),
    ("Useful tip: Use browser dev tools Network tab to check exact failing URLs and status codes for 404s.", "tip"),
    ("Idea: For future React apps in subdirectories, duplicate the build/copy steps in the workflow YAML.", "idea"),
    ("Idea: Use separate GitHub repos for each app to avoid subpath conflicts on Pages.", "idea"),
    ("Workflow: Edit code in VS Code, build with npm run build, copy dist to /docs, commit/push via VS Code Source Control.", "workflow"),
    ("Workflow: On push, GitHub Actions auto-builds, copies to /docs, commits update back to main.", "workflow")
    
    ]
    
    if len(thoughts) == 0:
        print("❌ No thoughts to add! Edit this file and paste your list.")
        sys.exit(1)
    
    add_thoughts(thoughts)