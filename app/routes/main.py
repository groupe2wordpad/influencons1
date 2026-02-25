from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..models import Article, Defi, SolidariteAction, ForumTopic, Newsletter
from .. import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    articles = Article.query.filter_by(is_published=True).order_by(Article.created_at.desc()).limit(3).all()
    defi = Defi.query.filter_by(is_active=True).order_by(Defi.created_at.desc()).first()
    solidarite = SolidariteAction.query.filter_by(is_active=True).order_by(SolidariteAction.is_featured.desc()).limit(4).all()
    topics = ForumTopic.query.filter_by(is_visible=True).order_by(ForumTopic.is_pinned.desc(), ForumTopic.created_at.desc()).limit(5).all()
    return render_template('index.html', articles=articles, defi=defi, solidarite=solidarite, topics=topics)

@main_bp.route('/article/<slug>')
def article(slug):
    art = Article.query.filter_by(slug=slug, is_published=True).first_or_404()
    recent = Article.query.filter_by(is_published=True).filter(Article.id != art.id).order_by(Article.created_at.desc()).limit(3).all()
    return render_template('article.html', article=art, recent=recent)

@main_bp.route('/articles')
def articles():
    page = request.args.get('page', 1, type=int)
    tag = request.args.get('tag', '')
    query = Article.query.filter_by(is_published=True)
    if tag:
        query = query.filter(Article.tag.ilike(f'%{tag}%'))
    articles = query.order_by(Article.created_at.desc()).paginate(page=page, per_page=6)
    return render_template('articles.html', articles=articles, current_tag=tag)

@main_bp.route('/newsletter', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email', '').strip()
    if not email or '@' not in email:
        flash('Email invalide.', 'error')
        return redirect(url_for('main.index') + '#newsletter')
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
