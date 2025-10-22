"""
Command-line interface for Cortex SDK.
Provides CLI commands for memory management operations.
"""

import click
import json
from pathlib import Path
from cortex import MemoryManager, MemoryConfig
from cortex.utils.schema import MemoryType, MemoryPriority, ForgetCriteria
from cortex.utils.logger import get_logger
import logging

logger = get_logger(__name__)


# Global config file path
CONFIG_FILE = Path.home() / ".cortex" / "config.json"


def load_config() -> dict:
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    """Save configuration to file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_memory_manager() -> MemoryManager:
    """Get configured memory manager instance."""
    config_dict = load_config()
    
    if not config_dict:
        click.echo("⚠️  No configuration found. Run 'cortex init' first.")
        raise click.Abort()
    
    config = MemoryConfig.from_dict(config_dict)
    return MemoryManager(config=config)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Cortex - Intelligent Memory Management System
    
    A powerful CLI for managing memories with semantic search,
    summarization, and flexible storage backends.
    """
    pass


@cli.command()
@click.option('--backend', default='local', type=click.Choice(['local', 'sqlite', 'pgvector']),
              help='Storage backend to use')
@click.option('--db-path', default='./cortex_memory.db', help='Database path (for sqlite)')
@click.option('--connection-string', help='Connection string (for pgvector)')
@click.option('--embedding-model', default='sentence-transformers/all-MiniLM-L6-v2',
              help='Embedding model to use')
def init(backend, db_path, connection_string, embedding_model):
    """Initialize Cortex configuration."""
    try:
        config = {
            'backend': backend,
            'db_path': db_path,
            'connection_string': connection_string,
            'embedding_model': embedding_model,
            'short_term_capacity': 1000,
            'long_term_capacity': 10000,
            'auto_summarize': True,
            'similarity_threshold': 0.5,
        }
        
        save_config(config)
        
        click.echo(f"✅ Cortex initialized with backend: {backend}")
        click.echo(f"📝 Config saved to: {CONFIG_FILE}")
        
    except Exception as e:
        click.echo(f"❌ Failed to initialize: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('content')
@click.option('--type', 'memory_type', default='short_term',
              type=click.Choice(['short_term', 'long_term']),
              help='Memory type')
@click.option('--tags', multiple=True, help='Memory tags')
@click.option('--priority', default='medium',
              type=click.Choice(['low', 'medium', 'high', 'critical']),
              help='Memory priority')
@click.option('--metadata', type=str, help='JSON metadata')
def remember(content, memory_type, tags, priority, metadata):
    """Store a new memory."""
    try:
        manager = get_memory_manager()
        
        # Parse metadata
        meta = {}
        if metadata:
            meta = json.loads(metadata)
        
        memory_id = manager.remember(
            content=content,
            memory_type=MemoryType(memory_type),
            tags=list(tags) if tags else [],
            priority=MemoryPriority(priority),
            metadata=meta
        )
        
        click.echo(f"✅ Memory stored: {memory_id}")
        click.echo(f"📝 Content: {content[:100]}...")
        
    except Exception as e:
        click.echo(f"❌ Failed to remember: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('query')
@click.option('--type', 'memory_type',
              type=click.Choice(['short_term', 'long_term']),
              help='Filter by memory type')
@click.option('--limit', default=10, help='Maximum results')
@click.option('--min-similarity', default=0.5, help='Minimum similarity score')
@click.option('--tags', multiple=True, help='Filter by tags')
@click.option('--json-output', is_flag=True, help='Output as JSON')
def recall(query, memory_type, limit, min_similarity, tags, json_output):
    """Recall memories matching a query."""
    try:
        manager = get_memory_manager()
        
        results = manager.recall(
            query=query,
            memory_type=MemoryType(memory_type) if memory_type else None,
            limit=limit,
            min_similarity=min_similarity,
            tags=list(tags) if tags else None
        )
        
        if json_output:
            output = []
            for result in results:
                output.append({
                    'id': result.memory.id,
                    'content': result.memory.content,
                    'similarity': result.similarity,
                    'rank': result.rank,
                    'tags': result.memory.tags,
                    'created_at': result.memory.created_at.isoformat()
                })
            click.echo(json.dumps(output, indent=2))
        else:
            if not results:
                click.echo("❌ No memories found.")
                return
            
            click.echo(f"\n🔍 Found {len(results)} memories:\n")
            
            for result in results:
                click.echo(f"  [{result.rank}] Similarity: {result.similarity:.3f}")
                click.echo(f"      ID: {result.memory.id}")
                click.echo(f"      Content: {result.memory.content[:150]}...")
                click.echo(f"      Tags: {', '.join(result.memory.tags)}")
                click.echo(f"      Created: {result.memory.created_at}")
                click.echo()
        
    except Exception as e:
        click.echo(f"❌ Failed to recall: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--topic', help='Topic to summarize')
@click.option('--type', 'memory_type',
              type=click.Choice(['short_term', 'long_term']),
              help='Filter by memory type')
@click.option('--tags', multiple=True, help='Filter by tags')
def summarize(topic, memory_type, tags):
    """Generate a summary of memories."""
    try:
        manager = get_memory_manager()
        
        summary = manager.summarize(
            topic=topic,
            memory_type=MemoryType(memory_type) if memory_type else None,
            tags=list(tags) if tags else None
        )
        
        click.echo("\n📊 Memory Summary\n")
        click.echo("=" * 60)
        click.echo(f"\n{summary.summary_text}\n")
        click.echo("=" * 60)
        click.echo(f"\n📈 Statistics:")
        click.echo(f"   Memories summarized: {summary.num_memories}")
        click.echo(f"   Topics: {', '.join(summary.topics) if summary.topics else 'None'}")
        
        if summary.time_range:
            click.echo(f"   Time range: {summary.time_range['start']} to {summary.time_range['end']}")
        
    except Exception as e:
        click.echo(f"❌ Failed to summarize: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--older-than', type=int, help='Days threshold')
@click.option('--relevance-threshold', type=float, help='Minimum relevance score')
@click.option('--type', 'memory_type',
              type=click.Choice(['short_term', 'long_term']),
              help='Filter by memory type')
@click.option('--tags', multiple=True, help='Filter by tags')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def forget(older_than, relevance_threshold, memory_type, tags, confirm):
    """Forget memories based on criteria."""
    try:
        if not confirm:
            click.confirm(
                '⚠️  This will permanently delete memories. Continue?',
                abort=True
            )
        
        manager = get_memory_manager()
        
        criteria = ForgetCriteria(
            older_than_days=older_than,
            relevance_threshold=relevance_threshold,
            memory_type=MemoryType(memory_type) if memory_type else None,
            tags=list(tags) if tags else None
        )
        
        count = manager.forget(criteria)
        
        click.echo(f"✅ Forgot {count} memories")
        
    except Exception as e:
        click.echo(f"❌ Failed to forget: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('memory_id')
def get(memory_id):
    """Get a specific memory by ID."""
    try:
        manager = get_memory_manager()
        
        memory = manager.get_memory(memory_id)
        
        if not memory:
            click.echo(f"❌ Memory not found: {memory_id}")
            return
        
        click.echo("\n📄 Memory Details\n")
        click.echo("=" * 60)
        click.echo(f"ID: {memory.id}")
        click.echo(f"Type: {memory.memory_type}")
        click.echo(f"Priority: {memory.priority}")
        click.echo(f"Relevance: {memory.relevance_score:.3f}")
        click.echo(f"Access Count: {memory.access_count}")
        click.echo(f"Tags: {', '.join(memory.tags)}")
        click.echo(f"Created: {memory.created_at}")
        click.echo(f"Updated: {memory.updated_at}")
        click.echo(f"\nContent:\n{memory.content}")
        click.echo("=" * 60)
        
        if memory.metadata:
            click.echo(f"\nMetadata:")
            click.echo(json.dumps(memory.metadata, indent=2))
        
    except Exception as e:
        click.echo(f"❌ Failed to get memory: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('memory_id')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def delete(memory_id, confirm):
    """Delete a specific memory."""
    try:
        if not confirm:
            click.confirm(f'⚠️  Delete memory {memory_id}?', abort=True)
        
        manager = get_memory_manager()
        
        success = manager.delete_memory(memory_id)
        
        if success:
            click.echo(f"✅ Memory deleted: {memory_id}")
        else:
            click.echo(f"❌ Memory not found: {memory_id}")
        
    except Exception as e:
        click.echo(f"❌ Failed to delete: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--json-output', is_flag=True, help='Output as JSON')
def stats(json_output):
    """Show memory statistics."""
    try:
        manager = get_memory_manager()
        
        stats_obj = manager.get_stats()
        
        if json_output:
            click.echo(stats_obj.json(indent=2))
        else:
            click.echo("\n📊 Memory Statistics\n")
            click.echo("=" * 60)
            click.echo(f"Total Memories: {stats_obj.total_memories}")
            click.echo(f"  Short-term: {stats_obj.short_term_count}")
            click.echo(f"  Long-term: {stats_obj.long_term_count}")
            click.echo(f"  Files: {stats_obj.file_count}")
            click.echo(f"\nAverage Relevance: {stats_obj.avg_relevance:.3f}")
            
            if stats_obj.oldest_memory:
                click.echo(f"Oldest Memory: {stats_obj.oldest_memory}")
            if stats_obj.newest_memory:
                click.echo(f"Newest Memory: {stats_obj.newest_memory}")
            
            click.echo("=" * 60)
        
    except Exception as e:
        click.echo(f"❌ Failed to get stats: {e}", err=True)
        raise click.Abort()


@cli.command()
def cleanup():
    """Clean up expired memories."""
    try:
        manager = get_memory_manager()
        
        count = manager.cleanup()
        
        click.echo(f"✅ Cleanup complete. Removed {count} expired memories.")
        
    except Exception as e:
        click.echo(f"❌ Failed to cleanup: {e}", err=True)
        raise click.Abort()


@cli.command()
def config():
    """Show current configuration."""
    try:
        config_dict = load_config()
        
        if not config_dict:
            click.echo("❌ No configuration found. Run 'cortex init' first.")
            return
        
        click.echo("\n⚙️  Cortex Configuration\n")
        click.echo("=" * 60)
        click.echo(json.dumps(config_dict, indent=2))
        click.echo("=" * 60)
        click.echo(f"\nConfig file: {CONFIG_FILE}")
        
    except Exception as e:
        click.echo(f"❌ Failed to show config: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()

