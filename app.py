from flask import Flask, render_template, request, send_file
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import tempfile

app = Flask(__name__)

G = ox.graph_from_xml('/home/rdksuper/map.osm')
G_proj = ox.project_graph(G)

ways = {}
for u, v, key, data in G_proj.edges(keys=True, data=True):
    name = None
    if 'name' in data:
        name = data['name']
    else:
        for key, value in data.items():
            if key not in ['length', 'geometry']:
                name = f"{key.capitalize()}: {value}"
                break
    if name:
        ways[(u, v, key)] = name

@app.route('/')
def index():
    return render_template('index.html', ways=ways)

@app.route('/plan_path', methods=['POST'])
def plan_path():
    start_way_name = request.form['start']
    end_way_name = request.form['end']
    
    start_way = next(way for way, name in ways.items() if name == start_way_name)
    end_way = next(way for way, name in ways.items() if name == end_way_name)
    
    start_node = start_way[0]
    end_node = end_way[1]
    
    try:
        path = nx.dijkstra_path(G_proj, start_node, end_node, weight='length')
        
        fig, ax = ox.plot_graph(G_proj, show=False, close=False)
        
        ax.scatter(G_proj.nodes[start_node]['x'], G_proj.nodes[start_node]['y'], c='green', s=50, zorder=5)
        ax.scatter(G_proj.nodes[end_node]['x'], G_proj.nodes[end_node]['y'], c='red', s=50, zorder=5)
        
        def animate(i):
            line = ax.plot([G_proj.nodes[node]['x'] for node in path[:i+1]],
                           [G_proj.nodes[node]['y'] for node in path[:i+1]],
                           c='blue', linewidth=2, zorder=4)
            return line
        
        anim = animation.FuncAnimation(fig, animate, frames=len(path), interval=200, blit=True, repeat=True)
        
        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as temp_file:
            anim.save(temp_file.name, writer='pillow', fps=5)
            temp_filename = temp_file.name

        plt.close(fig)
        
        return send_file(temp_filename, mimetype='image/gif')
    
    except nx.NetworkXNoPath:
        return "No path found between the selected ways.", 400

if __name__ == '__main__':
    app.run(debug=True)
