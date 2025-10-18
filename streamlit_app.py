"""
CHIPS Act Intelligence System - Streamlit Control App (MVP)
Core functionality for entity management, report generation, and progress tracking.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db import DatabaseOperations
from src.database.models import EntityType, CapabilityType, ReviewStatus


def init_session_state():
    """Initialize session state variables."""
    if 'db_ops' not in st.session_state:
        st.session_state.db_ops = DatabaseOperations()
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()


def get_entity_data():
    """Get entity data from database."""
    try:
        db_ops = st.session_state.db_ops
        entities = db_ops.get_all_entities()
        
        entity_data = []
        for entity in entities:
            # Get funding data
            funding_query = """
            SELECT SUM(amount) as total_funding, COUNT(*) as funding_count
            FROM funding WHERE entity_id = ?
            """
            funding_result = db_ops.db_manager.execute_query(funding_query, (entity.id,))
            total_funding = funding_result[0]['total_funding'] if funding_result and funding_result[0]['total_funding'] else 0
            funding_count = funding_result[0]['funding_count'] if funding_result else 0
            
            # Get capabilities
            capabilities_query = """
            SELECT capability_type FROM capabilities WHERE entity_id = ?
            """
            capabilities_result = db_ops.db_manager.execute_query(capabilities_query, (entity.id,))
            # Convert capability type integers to their string names (Official 6 Capabilities)
            capability_names = {
                1: "3D Packaging",
                2: "Heterogeneous Packaging", 
                3: "Multi Project Wafer",
                4: "Radio Frequency Integrated Circuit (RFIC) Design",
                5: "Monolithic Microwave Integrated Circuit (MMIC) Chips",
                6: "Radiation Hardened (RAD-HARD) Chips"
            }
            capabilities = [capability_names.get(row['capability_type'], f"Unknown ({row['capability_type']})") for row in capabilities_result]
            
            entity_data.append({
                'id': entity.id,
                'name': entity.name,
                'legal_name': entity.legal_name,
                'entity_type': entity.entity_type.value,
                'total_funding': total_funding,
                'funding_count': funding_count,
                'capabilities': ', '.join(capabilities) if capabilities else 'None',
                'capability_count': len(capabilities),
                'confidence_score': entity.confidence_score or 0.0,
                'created_at': entity.created_at.strftime('%Y-%m-%d') if entity.created_at else 'Unknown'
            })
        
        return pd.DataFrame(entity_data)
    except Exception as e:
        st.error(f"Error loading entity data: {e}")
        return pd.DataFrame()


def get_system_stats():
    """Get system statistics."""
    try:
        db_ops = st.session_state.db_ops
        stats = db_ops.get_database_stats()
        return stats
    except Exception as e:
        st.error(f"Error loading system stats: {e}")
        return {}


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="CHIPS Act Intelligence System",
        page_icon="🔬",
        layout="wide"
    )
    
    init_session_state()
    
    # Header
    st.title("🔬 CHIPS Act Intelligence System")
    st.markdown("**Control Center for Entity Discovery, Analysis & Report Generation**")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # System Status
        st.subheader("📊 System Status")
        stats = get_system_stats()
        
        if stats:
            total_entities = sum(stats.get('entities_by_type', {}).values())
            total_funding = stats.get('total_funding', 0)
            
            st.metric("Total Entities", total_entities)
            st.metric("Total Funding", f"${total_funding:,.0f}M")
            st.metric("Goal Progress", f"{total_entities}/100", f"{total_entities}%")
            
            # Progress bar
            progress = min(total_entities / 100, 1.0)
            st.progress(progress)
            
            if total_entities < 100:
                st.warning(f"Need {100 - total_entities} more entities to reach goal")
            else:
                st.success("🎉 Goal achieved!")
        
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("🔄 Refresh Data"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        
        if st.button("📊 Run Collection (CHIPS.gov)"):
            with st.spinner("Starting collection from CHIPS.gov..."):
                import subprocess
                import sys
                
                try:
                    # Run the collection system
                    result = subprocess.run([
                        sys.executable, "scripts/master_control.py", 
                        "--run-full", "--sources", "chips_gov"
                    ], capture_output=True, text=True, cwd=Path(__file__).parent)
                    
                    if result.returncode == 0:
                        st.success("Collection completed successfully!")
                        st.session_state.last_refresh = datetime.now()
                        st.rerun()
                    else:
                        st.error(f"Collection failed: {result.stderr}")
                except Exception as e:
                    st.error(f"Error running collection: {e}")
        
        if st.button("📊 Run Full Collection (All Sources)"):
            with st.spinner("Starting collection from all sources..."):
                import subprocess
                import sys
                
                try:
                    # Run the collection system with all sources
                    result = subprocess.run([
                        sys.executable, "scripts/master_control.py", 
                        "--run-full"
                    ], capture_output=True, text=True, cwd=Path(__file__).parent)
                    
                    if result.returncode == 0:
                        st.success("Full collection completed successfully!")
                        st.session_state.last_refresh = datetime.now()
                        st.rerun()
                    else:
                        st.error(f"Collection failed: {result.stderr}")
                except Exception as e:
                    st.error(f"Error running collection: {e}")
        
        if st.button("📄 Generate Reports"):
            with st.spinner("Generating reports..."):
                import subprocess
                import sys
                
                try:
                    # Run report generation
                    result = subprocess.run([
                        sys.executable, "scripts/generate_reports.py", "--all"
                    ], capture_output=True, text=True, cwd=Path(__file__).parent)
                    
                    if result.returncode == 0:
                        st.success("Reports generated successfully!")
                        st.session_state.last_refresh = datetime.now()
                        st.rerun()
                    else:
                        st.error(f"Report generation failed: {result.stderr}")
                except Exception as e:
                    st.error(f"Error generating reports: {e}")
    
    # Main Content
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🏢 Entities", "📄 Reports", "⚙️ Settings"])
    
    with tab1:
        st.header("📊 System Dashboard")
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Entities Found", total_entities if stats else 0)
        
        with col2:
            st.metric("Total Funding", f"${total_funding:,.0f}M" if stats else "$0M")
        
        with col3:
            entity_types = stats.get('entities_by_type', {})
            st.metric("Entity Types", len(entity_types))
        
        with col4:
            capabilities = stats.get('capabilities', {})
            st.metric("Capabilities", len(capabilities))
        
        # Entity Type Distribution
        if stats and 'entities_by_type' in stats:
            st.subheader("📈 Entity Type Distribution")
            entity_types_df = pd.DataFrame([
                {'Type': k, 'Count': v} for k, v in stats['entities_by_type'].items()
            ])
            
            fig = px.pie(entity_types_df, values='Count', names='Type', 
                        title="Entities by Type")
            st.plotly_chart(fig, use_container_width=True)
        
        # Funding Distribution
        if stats and 'top_entities_by_funding' in stats:
            st.subheader("💰 Top Entities by Funding")
            funding_df = pd.DataFrame(stats['top_entities_by_funding'])
            
            if not funding_df.empty:
                fig = px.bar(funding_df.head(10), x='name', y='total_funding',
                           title="Top 10 Entities by Funding")
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("🏢 Entity Management")
        
        # Entity Table
        entity_df = get_entity_data()
        
        if not entity_df.empty:
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                entity_types = ['All'] + list(entity_df['entity_type'].unique())
                selected_type = st.selectbox("Filter by Type", entity_types)
            
            with col2:
                min_funding = st.number_input("Min Funding ($M)", min_value=0, value=0)
            
            with col3:
                min_capabilities = st.number_input("Min Capabilities", min_value=0, value=0)
            
            # Apply filters
            filtered_df = entity_df.copy()
            if selected_type != 'All':
                filtered_df = filtered_df[filtered_df['entity_type'] == selected_type]
            filtered_df = filtered_df[filtered_df['total_funding'] >= min_funding * 1000000]
            filtered_df = filtered_df[filtered_df['capability_count'] >= min_capabilities]
            
            # Entity Table
            st.subheader(f"📋 Entities ({len(filtered_df)} found)")
            
            # Sort by funding
            filtered_df = filtered_df.sort_values('total_funding', ascending=False)
            
            # Display table
            st.dataframe(
                filtered_df[['name', 'entity_type', 'total_funding', 'capability_count', 'capabilities']],
                use_container_width=True,
                column_config={
                    'name': 'Entity Name',
                    'entity_type': 'Type',
                    'total_funding': st.column_config.NumberColumn('Funding ($)', format='$%.0f'),
                    'capability_count': 'Capabilities',
                    'capabilities': 'Capability List'
                }
            )
            
            # Entity Selection for Reports
            st.subheader("📄 Generate Reports")
            
            # Select entities
            selected_entities = st.multiselect(
                "Select entities for report generation:",
                options=filtered_df['name'].tolist(),
                default=filtered_df.head(5)['name'].tolist()
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Generate Selected Reports"):
                    if selected_entities:
                        with st.spinner(f"Generating reports for {len(selected_entities)} entities..."):
                            import subprocess
                            import sys
                            
                            try:
                                # Generate reports for selected entities
                                result = subprocess.run([
                                    sys.executable, "scripts/generate_reports.py", "--entities"
                                ], capture_output=True, text=True, cwd=Path(__file__).parent)
                                
                                if result.returncode == 0:
                                    st.success(f"Generated {len(selected_entities)} reports!")
                                    st.session_state.last_refresh = datetime.now()
                                    st.rerun()
                                else:
                                    st.error(f"Report generation failed: {result.stderr}")
                            except Exception as e:
                                st.error(f"Error generating reports: {e}")
                    else:
                        st.warning("Please select entities first")
            
            with col2:
                if st.button("📄 Generate All Reports"):
                    with st.spinner(f"Generating reports for all {len(filtered_df)} entities..."):
                        import subprocess
                        import sys
                        
                        try:
                            # Generate reports for all entities
                            result = subprocess.run([
                                sys.executable, "scripts/generate_reports.py", "--entities"
                            ], capture_output=True, text=True, cwd=Path(__file__).parent)
                            
                            if result.returncode == 0:
                                st.success(f"Generated {len(filtered_df)} reports!")
                                st.session_state.last_refresh = datetime.now()
                                st.rerun()
                            else:
                                st.error(f"Report generation failed: {result.stderr}")
                        except Exception as e:
                            st.error(f"Error generating reports: {e}")
            
            # Entity Prioritization
            st.subheader("🎯 Entity Prioritization")
            
            # Priority scoring
            priority_df = filtered_df.copy()
            priority_df['priority_score'] = (
                priority_df['total_funding'] / 1000000 * 0.4 +  # Funding weight
                priority_df['capability_count'] * 0.3 +         # Capability weight
                priority_df['confidence_score'] * 0.3           # Confidence weight
            )
            priority_df = priority_df.sort_values('priority_score', ascending=False)
            
            st.write("**Top Priority Entities:**")
            st.dataframe(
                priority_df.head(10)[['name', 'priority_score', 'total_funding', 'capability_count']],
                use_container_width=True,
                column_config={
                    'name': 'Entity Name',
                    'priority_score': st.column_config.NumberColumn('Priority Score', format='%.2f'),
                    'total_funding': st.column_config.NumberColumn('Funding ($)', format='$%.0f'),
                    'capability_count': 'Capabilities'
                }
            )
        
        else:
            st.warning("No entities found. Run collection to discover entities.")
    
    with tab3:
        st.header("📄 Report Management")
        
        # Report Status
        st.subheader("📊 Report Status")
        
        # Check for existing reports
        reports_dir = Path(__file__).parent / "reports"
        entity_reports_dir = reports_dir / "entities"
        cluster_reports_dir = reports_dir / "clusters"
        
        if entity_reports_dir.exists():
            entity_reports = list(entity_reports_dir.glob("*.md"))
            st.metric("Entity Reports", len(entity_reports))
        else:
            st.metric("Entity Reports", 0)
        
        if cluster_reports_dir.exists():
            cluster_reports = list(cluster_reports_dir.glob("*.md"))
            st.metric("Cluster Reports", len(cluster_reports))
        else:
            st.metric("Cluster Reports", 0)
        
        # Report Generation
        st.subheader("📄 Generate Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Generate Entity Reports"):
                with st.spinner("Generating entity reports..."):
                    import subprocess
                    import sys
                    
                    try:
                        # Generate entity reports
                        result = subprocess.run([
                            sys.executable, "scripts/generate_reports.py", "--entities"
                        ], capture_output=True, text=True, cwd=Path(__file__).parent)
                        
                        if result.returncode == 0:
                            st.success("Entity reports generated!")
                            st.session_state.last_refresh = datetime.now()
                            st.rerun()
                        else:
                            st.error(f"Entity report generation failed: {result.stderr}")
                    except Exception as e:
                        st.error(f"Error generating entity reports: {e}")
        
        with col2:
            if st.button("📄 Generate Cluster Reports"):
                with st.spinner("Generating cluster reports..."):
                    import subprocess
                    import sys
                    
                    try:
                        # Generate cluster reports
                        result = subprocess.run([
                            sys.executable, "scripts/generate_reports.py", "--clusters"
                        ], capture_output=True, text=True, cwd=Path(__file__).parent)
                        
                        if result.returncode == 0:
                            st.success("Cluster reports generated!")
                            st.session_state.last_refresh = datetime.now()
                            st.rerun()
                        else:
                            st.error(f"Cluster report generation failed: {result.stderr}")
                    except Exception as e:
                        st.error(f"Error generating cluster reports: {e}")
        
        # Report Download
        st.subheader("📥 Download Reports")
        
        if entity_reports_dir.exists() and entity_reports:
            st.write("**Available Entity Reports:**")
            
            # Format selection
            col1, col2 = st.columns([3, 1])
            with col2:
                report_format = st.selectbox(
                    "Report Format",
                    ["Markdown (.md)", "Word (.docx)", "Text (.txt)"],
                    key="report_format_selector"
                )
            
            # Convert format selection to file extension
            format_map = {
                "Markdown (.md)": ("md", "text/markdown"),
                "Word (.docx)": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                "Text (.txt)": ("txt", "text/plain")
            }
            
            selected_format, mime_type = format_map[report_format]
            
            for report in entity_reports[:10]:  # Show first 10
                try:
                    if selected_format == "md":
                        # Original markdown file
                        with open(report, 'r') as f:
                            content = f.read()
                        file_name = report.name
                    else:
                        # Convert to other format
                        from src.report_generator.format_converter import ReportFormatConverter
                        converter = ReportFormatConverter()
                        converted_path = converter.convert_report(str(report), selected_format)
                        
                        with open(converted_path, 'rb') as f:
                            content = f.read()
                        
                        # Update file name with new extension
                        file_name = report.stem + f".{selected_format}"
                    
                    st.download_button(
                        label=f"📄 {report.stem} ({selected_format.upper()})",
                        data=content,
                        file_name=file_name,
                        mime=mime_type,
                        key=f"download_{report.stem}_{selected_format}"
                    )
                except Exception as e:
                    st.error(f"Error converting {report.name} to {selected_format}: {e}")
    
    with tab4:
        st.header("⚙️ System Settings")
        
        # Collection Settings
        st.subheader("📡 Collection Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Data Sources:**")
            st.checkbox("CHIPS.gov", value=True, disabled=True)
            st.checkbox("SEC EDGAR", value=False)
            st.checkbox("University Press", value=False)
            st.checkbox("News Aggregators", value=False)
        
        with col2:
            st.write("**Collection Parameters:**")
            max_pages = st.slider("Max Pages per Source", 1, 50, 10)
            delay_range = st.slider("Delay Range (seconds)", 1, 30, (2, 10))
            st.write(f"Delay: {delay_range[0]}-{delay_range[1]} seconds")
        
        # Report Settings
        st.subheader("📄 Report Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Report Types:**")
            st.checkbox("Entity Reports", value=True)
            st.checkbox("Cluster Reports", value=True)
            st.checkbox("System Summary", value=True)
        
        with col2:
            st.write("**Report Format:**")
            st.checkbox("Markdown (.md)", value=True)
            st.checkbox("Word (.docx)", value=True)
            st.checkbox("Text (.txt)", value=True)
            st.checkbox("PDF", value=False)
        
        # System Info
        st.subheader("ℹ️ System Information")
        
        st.write(f"**Last Refresh:** {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"**Database Path:** {Path(__file__).parent / 'data' / 'chips_entities.db'}")
        st.write(f"**Reports Path:** {Path(__file__).parent / 'reports'}")


if __name__ == "__main__":
    main()
