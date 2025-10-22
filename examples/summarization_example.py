"""
Summarization Example for Cortex SDK

Demonstrates how to use the memory summarization features
to compress and distill important information from stored memories.
"""

from cortex import MemoryManager, MemoryConfig
from cortex.utils.schema import MemoryType, MemoryPriority
from datetime import datetime, timedelta


def main():
    print("=" * 70)
    print("Cortex SDK - Memory Summarization Example")
    print("=" * 70)
    print()
    
    # Initialize memory manager with lightweight config
    print("📦 Initializing Cortex Memory Manager...")
    config = MemoryConfig.lightweight()
    config.auto_summarize = True
    memory = MemoryManager(config=config, backend="local")
    print("✅ Memory Manager initialized\n")
    
    # Store sample memories about a project
    print("📝 Storing project-related memories...")
    
    project_memories = [
        "Project Alpha kick-off meeting scheduled for Monday at 10 AM with the dev team",
        "Decided to use Python and FastAPI for the backend API development",
        "Frontend will be built using React with TypeScript for type safety",
        "Database: PostgreSQL with pgvector extension for vector similarity search",
        "Sarah is the project lead, John handles backend, Emma works on frontend",
        "Target launch date is end of Q2, approximately 3 months from now",
        "Budget approved: $150,000 for development and infrastructure",
        "Must integrate with existing authentication system using OAuth2",
        "Performance requirement: API response time under 200ms for 95th percentile",
        "Security review scheduled for end of each sprint"
    ]
    
    memory_ids = []
    for idx, content in enumerate(project_memories):
        mem_id = memory.remember(
            content=content,
            memory_type=MemoryType.LONG_TERM,
            tags=["project-alpha", "planning"],
            priority=MemoryPriority.HIGH
        )
        memory_ids.append(mem_id)
        print(f"  ✓ Stored memory {idx + 1}/{len(project_memories)}")
    
    print(f"✅ Stored {len(memory_ids)} memories\n")
    
    # Get general summary
    print("📊 Generating general project summary...")
    print("-" * 70)
    
    summary = memory.summarize(
        tags=["project-alpha"]
    )
    
    print(f"\nSummary of {summary.num_memories} memories:")
    print(f"\n{summary.summary_text}\n")
    print(f"Topics: {', '.join(summary.topics)}")
    print("-" * 70)
    print()
    
    # Topic-specific summary
    print("🎯 Generating topic-specific summaries...\n")
    
    topics = ["team", "technical", "timeline"]
    
    for topic in topics:
        print(f"Topic: {topic.upper()}")
        print("-" * 70)
        
        topic_summary = memory.summarize(
            topic=topic,
            tags=["project-alpha"]
        )
        
        print(f"{topic_summary.summary_text}\n")
    
    # Store more memories with different tags
    print("📝 Storing additional memories...")
    
    additional_memories = [
        ("Sprint 1 completed: User authentication and basic CRUD operations", ["project-alpha", "sprints"]),
        ("Sprint 2 focus: Implement vector search and memory management features", ["project-alpha", "sprints"]),
        ("Code review revealed need for better error handling in API endpoints", ["project-alpha", "quality"]),
        ("Team feedback: Need better documentation for API endpoints", ["project-alpha", "quality"]),
        ("Performance testing shows database queries need optimization", ["project-alpha", "quality"])
    ]
    
    for content, tags in additional_memories:
        memory.remember(
            content=content,
            memory_type=MemoryType.LONG_TERM,
            tags=tags,
            priority=MemoryPriority.MEDIUM
        )
    
    print("✅ Additional memories stored\n")
    
    # Summary by tag
    print("🏷️  Summary by tag: 'sprints'")
    print("-" * 70)
    
    sprints_summary = memory.summarize(tags=["sprints"])
    print(f"{sprints_summary.summary_text}\n")
    
    print("🏷️  Summary by tag: 'quality'")
    print("-" * 70)
    
    quality_summary = memory.summarize(tags=["quality"])
    print(f"{quality_summary.summary_text}\n")
    
    # Get statistics
    print("📈 Memory Statistics:")
    print("-" * 70)
    
    stats = memory.get_stats()
    print(f"Total memories: {stats.total_memories}")
    print(f"Short-term: {stats.short_term_count}")
    print(f"Long-term: {stats.long_term_count}")
    print(f"Average relevance: {stats.avg_relevance:.3f}")
    print()
    
    # Demonstrate recall with summarization
    print("🔍 Recall memories about 'technical decisions':")
    print("-" * 70)
    
    results = memory.recall(
        query="What technical decisions were made for the project?",
        limit=5,
        min_similarity=0.3
    )
    
    if results:
        print(f"Found {len(results)} relevant memories:\n")
        for result in results:
            print(f"  [{result.rank}] Similarity: {result.similarity:.3f}")
            print(f"      {result.memory.content[:80]}...")
            print()
    
    # Cleanup
    print("🧹 Cleaning up expired memories...")
    removed = memory.cleanup()
    print(f"✅ Removed {removed} expired memories\n")
    
    print("=" * 70)
    print("✅ Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()

