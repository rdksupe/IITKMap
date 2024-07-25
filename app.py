from flask import Flask, render_template, request, send_file
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import io
import tempfile

app = Flask(__name__)


G = ox.graph_from_xml('/home/rdksuper/map.osm')
G_proj = ox.project_graph(G)

node_names = {}
for node, data in G_proj.nodes(data=True):
    if 'name' in data:
        node_names[node] = data['name']
    else:
        node_names[node] = f"Node at ({data['x']:.4f}, {data['y']:.4f})"

@app.route('/')
def index():
    return render_template('index.html', nodes=node_names)

@app.route('/plan_path', methods=['POST'])
def plan_path():
    start_node = int(request.form['start'])
    end_node = int(request.form['end'])
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
        return "No path found between the selected nodes.", 400

if __name__ == '__main__':
    app.run(debug=True)