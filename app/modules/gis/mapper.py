import folium
from folium.plugins import MarkerCluster
from typing import List, Dict, Any, Optional
from app.models.issue import Issue, PriorityLevel

class GISMapGenerator:
    """
    GIS Geotagged Map Engine:
    - Generates Leaflet/Folium interactive maps with marker clusters
    - Visualizes priority-coded pins and popups
    - Supports HTML export and GeoJSON layer generation
    """

    COLOR_MAP = {
        PriorityLevel.CRITICAL: "red",
        PriorityLevel.HIGH: "orange",
        PriorityLevel.MEDIUM: "blue",
        PriorityLevel.LOW: "green"
    }

    def generate_folium_map(
        self,
        issues: List[Issue],
        center_lat: float = 19.0760,
        center_lng: float = 72.8777,
        zoom_start: int = 12
    ) -> folium.Map:
        fmap = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom_start,
            tiles="CartoDB positron"
        )
        marker_cluster = MarkerCluster(name="Civic Issue Clusters").add_to(fmap)

        for issue in issues:
            color = self.COLOR_MAP.get(issue.priorityLevel, "gray")
            popup_html = f"""
            <div style="font-family: sans-serif; font-size: 13px; min-width: 220px;">
                <h4 style="margin: 0 0 6px; color: #1e293b;">{issue.issueId}</h4>
                <p style="margin: 0 0 4px;"><b>Category:</b> {issue.category.value}</p>
                <p style="margin: 0 0 4px;"><b>Priority:</b> <span style="color: {color}; font-weight: bold;">{issue.priorityLevel.value} ({issue.priorityScore:.2f})</span></p>
                <p style="margin: 0 0 4px;"><b>Location:</b> {issue.location}</p>
                <p style="margin: 0 0 4px;"><b>Status:</b> {issue.status.value}</p>
                <p style="margin: 0 0 4px;"><b>Action:</b> {issue.recommendedAction}</p>
            </div>
            """
            folium.Marker(
                location=[issue.latitude, issue.longitude],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{issue.issueId} - {issue.category.value} ({issue.priorityLevel.value})",
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(marker_cluster)

        return fmap

    def generate_map_html(self, issues: List[Issue]) -> str:
        fmap = self.generate_folium_map(issues)
        return fmap._repr_html_()

gis_mapper = GISMapGenerator()
