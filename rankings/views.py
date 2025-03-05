from django.shortcuts import render
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import json
import os
from django.conf import settings

# Create your views here
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def upload_file(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Only POST requests are allowed'})
            
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'No file uploaded'})
        
        # Read CSV file
        df = pd.read_csv(file)
        required_columns = {'Name', 'PhD University', 'Current University'}
        if not required_columns.issubset(df.columns):
            return JsonResponse({'error': 'CSV must contain Name, PhD University, and Current University columns'})
        
        # Create graph and calculate rankings
        G = create_university_graph(df)
        rankings = calculate_rankings(G)
        
        # Create visualization
        visualization = create_network_visualization(G, rankings)
        
        return JsonResponse({
            'rankings': rankings,
            'visualization': visualization
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)})

def create_university_graph(df):
    # Create directed graph
    G = nx.DiGraph()
    
    # Get set of all current universities
    current_universities = set(df['Current University'].unique())
    
    # Add edges from PhD university to current university
    for _, row in df.iterrows():
        phd_univ = row['PhD University']
        current_univ = row['Current University']
        # Only add edge if PhD university exists in current universities list
        if phd_univ != current_univ and phd_univ in current_universities:
            if G.has_edge(current_univ, phd_univ):
                G[current_univ][phd_univ]['weight'] += 1
            else:
                G.add_edge(current_univ, phd_univ, weight=1)
    
    return G

def calculate_rankings(G):
    # Calculate PageRank
    pagerank = nx.pagerank(G, weight='weight')
    
    # Sort universities by PageRank score
    rankings = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
    return rankings

def create_network_visualization(G, rankings):
    # Create node positions using spring layout
    pos = nx.spring_layout(G)
    
    # Create edges data
    edge_traces = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_traces.append({
            'x': [x0, x1, None],
            'y': [y0, y1, None]
        })
    
    # Create nodes data
    node_data = {
        'x': [],
        'y': [],
        'text': [],
        'labels': []
    }
    
    for node in G.nodes():
        x, y = pos[node]
        node_data['x'].append(x)
        node_data['y'].append(y)
        node_data['labels'].append(node)
        node_data['text'].append(f"{node}<br>Rank: {next((i+1 for i, (n, _) in enumerate(rankings) if n == node), 0)}")
    
    return {
        'edges': edge_traces,
        'nodes': node_data
    }
# Create your views here.
