
from flask import Flask, render_template, request
from model.recommend import recomendar_producto

# Create the application.
app = Flask(__name__)

# Serve the index page.
@app.route('/')
def index():
    template = 'index.html'
    return render_template(template)

# Serve the home page.
@app.route('/home', methods=['GET', 'POST'])
def home():
    template = 'home.html'
    if request.method == 'POST':

        user: str = request.form.get('user', None)
        
        if not user:
            return render_template(template, error="Debes ingresar un usuario")

        recommended_products =  recomendar_producto(user)

        if not recommended_products:
            return render_template(template, error=f"No se han encontrado productos recomendados para el usuario ${user}")
        
        return render_template(template, user=user, products=recommended_products)

    return render_template(template)

# Run the application.
if __name__ == '__main__':
    app.run(debug=True, static_folder='static')