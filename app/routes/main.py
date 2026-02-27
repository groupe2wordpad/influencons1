from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import Article, Defi, SolidariteAction, Newsletter

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Derniers articles
    articles = Article.query.filter_by(is_published=True).order_by(Article.created_at.desc()).limit(6).all()
    
    # Défi actif
    defi = Defi.query.filter_by(is_active=True).order_by(Defi.created_at.desc()).first()
    
    # Actions de solidarité
    solidarite = SolidariteAction.query.filter_by(is_active=True).order_by(SolidariteAction.is_featured.desc()).limit(4).all()
    
    return render_template('index.html', articles=articles, defi=defi, solidarite=solidarite)

# Redirection ancienne route articles → index
@main_bp.route('/articles')
def articles_redirect():
    return redirect(url_for('main.index') + "#articles")

# Redirection article unique → index
@main_bp.route('/article/<slug>')
def article_redirect(slug):
    # Ici tu peux ajouter un paramètre pour scroller vers l'article si tu veux
    return redirect(url_for('main.index') + f"#article-{slug}")

# Newsletter
@main_bp.route('/newsletter', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email', '').strip()
    if not email or '@' not in email:
        flash('Email invalide.', 'error')
        return redirect(url_for('main.index') + '#newsletter')
    from .. import db
    existing = Newsletter.query.filter_by(email=email).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.session.commit()
            flash('Vous êtes de nouveau abonné(e) ! ✦', 'success')
        else:
            flash('Vous êtes déjà abonné(e) !', 'info')
    else:
        sub = Newsletter(email=email)
        db.session.add(sub)
        db.session.commit()
        flash('Merci ! Vous êtes maintenant abonné(e) ✦', 'success')
    return redirect(url_for('main.index') + '#newsletter')
