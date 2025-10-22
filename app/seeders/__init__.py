from .comment_seeder import run as seed_comments

def run_all():
    """Ejecuta todos los seeders del proyecto."""
    print("Ejecutando todos los seeders...")
    seed_comments()
    print("Todos los seeders ejecutados correctamente.")