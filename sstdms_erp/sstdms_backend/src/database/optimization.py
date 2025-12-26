# optimization.py

import sqlite3
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

class DatabaseOptimizer:
    """Database optimization and performance monitoring system."""
    
    def __init__(self, db_path: str = "./src/database/app.db"):
        self.db_path = db_path
        self.performance_log = []
    
    def analyze_database(self) -> Dict[str, Any]:
        """Analyze database structure and performance."""
        analysis_results = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            db_size = page_count * page_size
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_info = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                table_info[table] = {
                    "row_count": row_count,
                    "column_count": len(columns),
                    "columns": [{"name": col[1], "type": col[2]} for col in columns]
                }
            
            # Get index information
            cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
            indexes = cursor.fetchall()
            
            analysis_results = {
                "database_size": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "page_count": page_count,
                "page_size": page_size,
                "table_count": len(tables),
                "tables": table_info,
                "indexes": [{"name": idx[0], "table": idx[1]} for idx in indexes],
                "analyzed_at": datetime.now().isoformat()
            }
        
        return analysis_results
    
    def optimize_database(self) -> Dict[str, Any]:
        """Perform comprehensive database optimization."""
        optimization_results = {
            "started_at": datetime.now().isoformat(),
            "operations": []
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Update table statistics
            start_time = time.time()
            cursor.execute("ANALYZE")
            analyze_time = time.time() - start_time
            optimization_results["operations"].append({
                "operation": "ANALYZE",
                "duration": round(analyze_time, 3),
                "description": "Updated table statistics for query optimizer"
            })
            
            # 2. Vacuum database to reclaim space
            start_time = time.time()
            cursor.execute("VACUUM")
            vacuum_time = time.time() - start_time
            optimization_results["operations"].append({
                "operation": "VACUUM",
                "duration": round(vacuum_time, 3),
                "description": "Reclaimed unused space and defragmented database"
            })
            
            # 3. Optimize query planner
            start_time = time.time()
            cursor.execute("PRAGMA optimize")
            optimize_time = time.time() - start_time
            optimization_results["operations"].append({
                "operation": "PRAGMA optimize",
                "duration": round(optimize_time, 3),
                "description": "Optimized query planner statistics"
            })
            
            conn.commit()
        
        optimization_results["completed_at"] = datetime.now().isoformat()
        optimization_results["total_duration"] = round(
            analyze_time + vacuum_time + optimize_time, 3
        )
        
        return optimization_results
    
    def create_recommended_indexes(self) -> List[Dict[str, str]]:
        """Create recommended indexes based on common query patterns."""
        recommended_indexes = [
            {
                "table": "users_enhanced",
                "index_name": "idx_users_enhanced_username_active",
                "sql": "CREATE INDEX IF NOT EXISTS idx_users_enhanced_username_active ON users_enhanced(username, is_active)",
                "reason": "Optimize login queries"
            },
            {
                "table": "users_enhanced",
                "index_name": "idx_users_enhanced_email_active",
                "sql": "CREATE INDEX IF NOT EXISTS idx_users_enhanced_email_active ON users_enhanced(email, is_active)",
                "reason": "Optimize email-based lookups"
            },
            {
                "table": "projects_enhanced",
                "index_name": "idx_projects_enhanced_status_created_by",
                "sql": "CREATE INDEX IF NOT EXISTS idx_projects_enhanced_status_created_by ON projects_enhanced(status, created_by)",
                "reason": "Optimize project listing by status and owner"
            },
            {
                "table": "documents_enhanced",
                "index_name": "idx_documents_enhanced_project_status",
                "sql": "CREATE INDEX IF NOT EXISTS idx_documents_enhanced_project_status ON documents_enhanced(project_id, status)",
                "reason": "Optimize document queries by project and status"
            },
            {
                "table": "audit_log",
                "index_name": "idx_audit_log_user_action_date",
                "sql": "CREATE INDEX IF NOT EXISTS idx_audit_log_user_action_date ON audit_log(user_id, action, created_at)",
                "reason": "Optimize audit log queries"
            },
            {
                "table": "notifications",
                "index_name": "idx_notifications_user_read_date",
                "sql": "CREATE INDEX IF NOT EXISTS idx_notifications_user_read_date ON notifications(user_id, is_read, created_at)",
                "reason": "Optimize notification queries"
            }
        ]
        
        created_indexes = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for index_info in recommended_indexes:
                try:
                    cursor.execute(index_info["sql"])
                    created_indexes.append({
                        "index_name": index_info["index_name"],
                        "table": index_info["table"],
                        "reason": index_info["reason"],
                        "status": "created"
                    })
                except sqlite3.Error as e:
                    created_indexes.append({
                        "index_name": index_info["index_name"],
                        "table": index_info["table"],
                        "reason": index_info["reason"],
                        "status": f"failed: {str(e)}"
                    })
            
            conn.commit()
        
        return created_indexes
    
    def monitor_query_performance(self, query: str, params: tuple = ()) -> Dict[str, Any]:
        """Monitor and log query performance."""
        start_time = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enable query plan logging
            cursor.execute("PRAGMA query_only = ON")
            
            try:
                # Execute query
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = cursor.fetchall()
                execution_time = time.time() - start_time
                
                # Get query plan
                explain_query = f"EXPLAIN QUERY PLAN {query}"
                cursor.execute(explain_query, params)
                query_plan = cursor.fetchall()
                
                performance_data = {
                    "query": query,
                    "params": params,
                    "execution_time": round(execution_time, 4),
                    "result_count": len(results),
                    "query_plan": [{"id": row[0], "parent": row[1], "detail": row[3]} for row in query_plan],
                    "timestamp": datetime.now().isoformat()
                }
                
                self.performance_log.append(performance_data)
                
                return performance_data
                
            except sqlite3.Error as e:
                return {
                    "query": query,
                    "params": params,
                    "error": str(e),
                    "execution_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                }
            finally:
                cursor.execute("PRAGMA query_only = OFF")
    
    def get_slow_queries(self, threshold_seconds: float = 0.1) -> List[Dict[str, Any]]:
        """Get queries that exceed the performance threshold."""
        slow_queries = [
            log for log in self.performance_log 
            if log.get("execution_time", 0) > threshold_seconds
        ]
        
        # Sort by execution time (slowest first)
        slow_queries.sort(key=lambda x: x.get("execution_time", 0), reverse=True)
        
        return slow_queries
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.performance_log:
            return {"error": "No performance data available"}
        
        total_queries = len(self.performance_log)
        total_time = sum(log.get("execution_time", 0) for log in self.performance_log)
        avg_time = total_time / total_queries if total_queries > 0 else 0
        
        # Find slowest queries
        slowest_queries = sorted(
            self.performance_log, 
            key=lambda x: x.get("execution_time", 0), 
            reverse=True
        )[:5]
        
        # Query frequency analysis
        query_frequency = {}
        for log in self.performance_log:
            query = log.get("query", "")
            if query in query_frequency:
                query_frequency[query] += 1
            else:
                query_frequency[query] = 1
        
        most_frequent = sorted(
            query_frequency.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            "summary": {
                "total_queries": total_queries,
                "total_execution_time": round(total_time, 4),
                "average_execution_time": round(avg_time, 4),
                "report_generated": datetime.now().isoformat()
            },
            "slowest_queries": slowest_queries,
            "most_frequent_queries": [
                {"query": query, "frequency": freq} 
                for query, freq in most_frequent
            ],
            "slow_query_count": len(self.get_slow_queries()),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on performance data."""
        recommendations = []
        
        slow_queries = self.get_slow_queries()
        if slow_queries:
            recommendations.append(
                f"Found {len(slow_queries)} slow queries. Consider adding indexes or optimizing query structure."
            )
        
        if len(self.performance_log) > 1000:
            recommendations.append(
                "Large number of queries logged. Consider implementing query caching."
            )
        
        # Analyze query patterns
        select_queries = [log for log in self.performance_log if log.get("query", "").strip().upper().startswith("SELECT")]
        if len(select_queries) > len(self.performance_log) * 0.8:
            recommendations.append(
                "High ratio of SELECT queries. Consider implementing read replicas for better performance."
            )
        
        return recommendations
    
    def export_performance_data(self, output_file: str = None) -> str:
        """Export performance data to JSON file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"performance_data_{timestamp}.json"
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "performance_log": self.performance_log,
            "performance_report": self.generate_performance_report()
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Performance data exported to: {output_file}")
        return output_file
    
    def clear_performance_log(self):
        """Clear the performance log."""
        self.performance_log.clear()
        print("Performance log cleared")

# Example usage and testing
if __name__ == "__main__":
    # Initialize optimizer
    optimizer = DatabaseOptimizer()
    
    # Analyze database
    analysis = optimizer.analyze_database()
    print("Database Analysis:")
    print(f"  Size: {analysis['database_size_mb']} MB")
    print(f"  Tables: {analysis['table_count']}")
    print(f"  Indexes: {len(analysis['indexes'])}")
    
    # Create recommended indexes
    print("\nCreating recommended indexes...")
    created_indexes = optimizer.create_recommended_indexes()
    for index in created_indexes:
        print(f"  {index['index_name']}: {index['status']}")
    
    # Optimize database
    print("\nOptimizing database...")
    optimization_results = optimizer.optimize_database()
    print(f"  Total duration: {optimization_results['total_duration']} seconds")
    
    # Test query performance monitoring
    print("\nTesting query performance monitoring...")
    test_queries = [
        "SELECT COUNT(*) FROM users_enhanced",
        "SELECT * FROM users_enhanced WHERE is_active = 1 LIMIT 10",
        "SELECT COUNT(*) FROM projects_enhanced"
    ]
    
    for query in test_queries:
        perf_data = optimizer.monitor_query_performance(query)
        print(f"  Query: {query[:50]}... - {perf_data.get('execution_time', 0)} seconds")
    
    # Generate performance report
    report = optimizer.generate_performance_report()
    print(f"\nPerformance Report:")
    print(f"  Total queries: {report['summary']['total_queries']}")
    print(f"  Average time: {report['summary']['average_execution_time']} seconds")
    
    # Export performance data
    export_file = optimizer.export_performance_data()
    print(f"Performance data exported to: {export_file}")

