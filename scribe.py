#!/usr/bin/env python3
"""
Scribe - A local knowledge companion
Search your personal notes like a tiny AI assistant.
"""

import argparse
import difflib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ============================================
# Helpers
# ============================================

class SimpleStemmer:
    """Very lightweight stemming for common English words."""

    @staticmethod
    def stem(word):
        word = word.lower()
        suffixes = [
            ('tion', ''), ('sion', ''), ('ing', ''), ('ed', ''), ('ly', ''),
            ('ous', ''), ('ful', ''), ('less', ''), ('ness', ''), ('ment', ''),
            ('able', ''), ('ible', ''), ('al', ''), ('ic', ''), ('ity', ''),
            ('er', ''), ('est', ''), ('s', '')
        ]
        for suffix, replace in suffixes:
            if word.endswith(suffix):
                return word[:-len(suffix)] + replace
        return word


SYNONYMS = {
    'python': ['py', 'programming', 'code'],
    'linux': ['ubuntu', 'debian', 'unix', 'terminal', 'bash'],
    'install': ['setup', 'download', 'configure'],
    'help': ['assist', 'guide', 'tutorial'],
    'error': ['bug', 'problem', 'issue', 'fail'],
    'file': ['document', 'text', 'data'],
    'search': ['find', 'query', 'look'],
    'learn': ['study', 'understand', 'know'],
    'note': ['notes', 'memo', 'idea'],
}


class KnowledgeBase:
    def __init__(self, folder="./notes"):
        self.folder = Path(folder)
        self.folder.mkdir(exist_ok=True)
        self.index = defaultdict(list)
        self.file_meta = {}
        self.stemmer = SimpleStemmer()

    def load_files(self):
        files = []
        for path in self.folder.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".txt", ".md", ".json", ".csv"}:
                files.append(path)
        return sorted(files)

    def build_index(self):
        self.index = defaultdict(list)
        self.file_meta = {}

        for path in self.load_files():
            try:
                text = path.read_text(encoding='utf-8', errors='ignore')
                lines = text.splitlines()

                self.file_meta[str(path)] = {
                    'name': path.name,
                    'size': len(text),
                    'lines': len(lines),
                    'modified': path.stat().st_mtime,
                }

                words = set(re.findall(r"\b\w+\b", text.lower()))
                for word in words:
                    stemmed = self.stemmer.stem(word)
                    self.index[stemmed].append(str(path))
            except Exception as e:
                print(f"Error reading {path}: {e}", file=sys.stderr)

        return len(self.file_meta)

    def _expand_query(self, query):
        qwords = set(re.findall(r"\b\w+\b", query.lower()))
        expanded = set()

        for word in qwords:
            expanded.add(word)
            expanded.add(self.stemmer.stem(word))
            for alias in SYNONYMS.get(word, []):
                expanded.add(alias)
                expanded.add(self.stemmer.stem(alias))

        return expanded

    def search(self, query, top_k=5, mode='smart'):
        if mode == 'exact':
            return self._search_exact(query, top_k)
        elif mode == 'fuzzy':
            return self._search_fuzzy(query, top_k)
        return self._search_smart(query, top_k)

    def _search_exact(self, query, top_k):
        words = self._expand_query(query)
        file_scores = defaultdict(int)

        for word in words:
            for file_path in self.index.get(word, []):
                file_scores[file_path] += 1

        return self._rank_results(file_scores, top_k)

    def _search_fuzzy(self, query, top_k):
        words = self._expand_query(query)
        file_scores = defaultdict(int)

        for qword in words:
            for index_word, paths in self.index.items():
                if not index_word:
                    continue
                ratio = difflib.SequenceMatcher(None, qword, index_word).ratio()
                if ratio > 0.6:
                    for path in paths:
                        file_scores[path] += int(ratio * 12)

        return self._rank_results(file_scores, top_k)

    def _search_smart(self, query, top_k):
        words = self._expand_query(query)
        file_scores = defaultdict(int)

        for word in words:
            for path in self.index.get(word, []):
                file_scores[path] += 1

        # boost files if query title words appear in filename or text
        for path, meta in self.file_meta.items():
            name = meta['name'].lower()
            if any(word in name for word in re.findall(r"\b\w+\b", query.lower())):
                file_scores[path] += 3

        return self._rank_results(file_scores, top_k)

    def _rank_results(self, scores, top_k):
        if not scores:
            return []

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for file_path, score in ranked:
            results.append({
                'path': file_path,
                'name': self.file_meta.get(file_path, {}).get('name', 'unknown'),
                'score': score,
                'relevance': min(100, score * 20),
            })
        return results

    def extract_snippets(self, file_path, query, context=2, max_snippets=3):
        path = Path(file_path)
        try:
            text = path.read_text(encoding='utf-8', errors='ignore')
            lines = text.splitlines()
        except Exception:
            return []

        expanded = set()
        for word in re.findall(r"\b\w+\b", query.lower()):
            expanded.add(word)
            expanded.add(self.stemmer.stem(word))

        snippets = []
        for i, line in enumerate(lines):
            lower = line.lower()
            if any(word in lower for word in expanded):
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                snippet = "\n".join(lines[start:end])
                snippets.append(snippet)

        return snippets[:max_snippets]

    def add_note(self, content, filename=None):
        if filename is None:
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'note_{stamp}.txt'

        path = self.folder / filename
        path.write_text(content, encoding='utf-8')
        self.build_index()
        return str(path)


class ScribeCLI:
    def __init__(self, kb):
        self.kb = kb
        self.kb.build_index()

    def _highlight_query(self, text, query):
        query_words = set(re.findall(r"\b\w+\b", query.lower()))
        words = text.split()
        highlighted = []

        for word in words:
            w = word.lower().strip('.,!?;:()[]{}"\'')
            if w in query_words or self.kb.stemmer.stem(w) in {self.kb.stemmer.stem(q) for q in query_words}:
                highlighted.append(f"**{word}**")
            else:
                highlighted.append(word)

        out = ' '.join(highlighted)
        out = out.replace('\n', ' | ')
        return out[:200] + '...' if len(out) > 200 else out

    def format_answer(self, query, results):
        if not results:
            return (
                f"\n❌ I couldn’t find anything useful about '{query}' in your notes.\n\n"
                "Try a more specific question, or add a note with the right keywords.\n"
            )

        answer = f"\n✨ I found {len(results)} likely match(es):\n"

        for i, result in enumerate(results, 1):
            answer += f"\n📄 {i}. {result['name']} (confidence {result['relevance']:.0f}%)\n"
            snippets = self.kb.extract_snippets(result['path'], query)
            if snippets:
                for snippet in snippets[:2]:
                    answer += f"   └─ {self._highlight_query(snippet, query)}\n"
            else:
                answer += "   └─ No snippet matched closely enough.\n"

        answer += "\n💡 Want a more specific answer? Ask again with a clearer question.\n"
        return answer

    def single_query(self, query, mode='smart', top_k=5):
        print(f"\n🔍 Searching for: '{query}'\n")
        results = self.kb.search(query, top_k=top_k, mode=mode)
        print(self.format_answer(query, results))

    def interactive(self):
        print("\n" + "=" * 60)
        print("📝 Scribe - your local knowledge companion")
        print("=" * 60)
        print(f"📚 Indexed {len(self.kb.load_files())} file(s)")
        print("Type 'exit' or 'quit' to leave.\n")

        while True:
            try:
                query = input("You: ").strip()
            except KeyboardInterrupt:
                print("\n\nGoodbye.\n")
                break

            if query.lower() in {'exit', 'quit', 'bye'}:
                print("\nGoodbye.\n")
                break
            if not query:
                continue

            results = self.kb.search(query, top_k=3, mode='smart')
            print(self.format_answer(query, results))


def main():
    parser = argparse.ArgumentParser(
        description='Scribe - a local knowledge companion that searches your notes',
        epilog='''Examples:\n  scribe --query "How do I use Python?"\n  scribe --interactive\n  scribe --add "Learning Linux is fun."\n  scribe --folder ./notes --query "terminal commands"'''
    )
    parser.add_argument('--folder', default='./notes', help='Folder with notes (.txt, .md, .json)')
    parser.add_argument('--query', help='Ask a question based on your notes')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive prompt loop')
    parser.add_argument('--add', help='Add a note directly to the knowledge base')
    parser.add_argument('--mode', choices=['smart', 'fuzzy', 'exact'], default='smart', help='Search strategy')
    parser.add_argument('--top-k', type=int, default=5, help='Maximum number of results to show')
    parser.add_argument('--index-only', action='store_true', help='Just build the index and exit')

    args = parser.parse_args()
    kb = KnowledgeBase(folder=args.folder)
    cli = ScribeCLI(kb)

    if args.index_only:
        count = kb.build_index()
        print(f"✅ Indexed {count} file(s) in {args.folder}")
        return

    if args.add:
        path = kb.add_note(args.add)
        print(f"✅ Saved a note to: {path}")
        return

    if args.interactive:
        cli.interactive()
        return

    if args.query:
        cli.single_query(args.query, mode=args.mode, top_k=args.top_k)
        return

    parser.print_help()


if __name__ == '__main__':
    main()
