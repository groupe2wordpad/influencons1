from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from ..models import User, Article, Defi, SolidariteAction, ForumTopic, Newsletter
from .. import db
import re, datetime, os, uuid
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__)

# ── UTILITAIRES ──
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def save_image(file):
    if file and file.filename and '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(UPLOAD_FOLDER, unique_name))
            return f"/static/uploads/{unique_name}"
    return None

# ── AUTH ──
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, is_admin=True).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('Email ou mot de passe incorrect.', 'error')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

# ── DASHBOARD ──
@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'articles':    Article.query.count(),
        'defis':       Defi.query.count(),
        'solidarite':  SolidariteAction.query.count(),
        'topics':      ForumTopic.query.count(),
        'subscribers': Newsletter.query.filter_by(is_active=True).count(),
    }
    recent_articles    = Article.query.order_by(Article.created_at.desc()).limit(5).all()
    recent_subscribers = Newsletter.query.order_by(Newsletter.created_at.desc()).limit(5).all()
    recent_defis       = Defi.query.order_by(Defi.created_at.desc()).limit(5).all()
    recent_solidarite  = SolidariteAction.query.order_by(SolidariteAction.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
        stats=stats,
        recent_articles=recent_articles,
        recent_subscribers=recent_subscribers,
        recent_defis=recent_defis,
        recent_solidarite=recent_solidarite
    )

# ── ARTICLES ──
@admin_bp.route('/articles')
@admin_required
def articles():
    items = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('admin/articles.html', items=items)

@admin_bp.route('/articles/new', methods=['GET', 'POST'])
@admin_required
def article_new():
    if request.method == 'POST':
        title = request.form.get('title')
        slug = slugify(title)
        base_slug = slug
        counter = 1
        while Article.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Gestion image upload OU URL
        image_file = request.files.get('image_url')
        image = save_image(image_file) or request.form.get('image_url_text')

        art = Article(
            title=title,
            slug=slug,
            tag=request.form.get('tag'),
            excerpt=request.form.get('excerpt'),
            content=request.form.get('content'),
            image_url=image,
            is_published=bool(request.form.get('is_published'))
        )
        db.session.add(art)
        db.session.commit()
        flash('Article publié avec succès ✦', 'success')
        return redirect(url_for('admin.articles'))
    return render_template('admin/article_form.html', item=None)

@admin_bp.route('/articles/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def article_edit(id):
    art = Article.query.get_or_404(id)
    if request.method == 'POST':
        art.title      = request.form.get('title')
        art.tag        = request.form.get('tag')
        art.excerpt    = request.form.get('excerpt')
        art.content    = request.form.get('content')
        art.is_published = bool(request.form.get('is_published'))
        art.updated_at = datetime.datetime.utcnow()

        # Gestion image : nouveau fichier uploadé prioritaire, sinon URL texte, sinon on garde l'existante
        image_file = request.files.get('image_url')
        if image_file and image_file.filename:
            art.image_url = save_image(image_file)
        elif request.form.get('image_url_text'):
            art.image_url = request.form.get('image_url_text')

        db.session.commit()
        flash('Article mis à jour ✦', 'success')
        return redirect(url_for('admin.articles'))
    return render_template('admin/article_form.html', item=art)

@admin_bp.route('/articles/<int:id>/delete', methods=['POST'])
@admin_required
def article_delete(id):
    art = Article.query.get_or_404(id)
    db.session.delete(art)
    db.session.commit()
    flash('Article supprimé.', 'info')
    return redirect(url_for('admin.articles'))

# ── DÉFIS ──
@admin_bp.route('/defis')
@admin_required
def defis():
    items = Defi.query.order_by(Defi.created_at.desc()).all()
    return render_template('admin/defis.html', items=items)

@admin_bp.route('/defis/new', methods=['GET', 'POST'])
@admin_required
def defi_new():
    if request.method == 'POST':
        image_file = request.files.get('image_url')
        image = save_image(image_file) or request.form.get('image_url_text')

        defi = Defi(
            title=request.form.get('title'),
            description=request.form.get('description'),
            step1_title=request.form.get('step1_title'),
            step1_desc=request.form.get('step1_desc'),
            step2_title=request.form.get('step2_title'),
            step2_desc=request.form.get('step2_desc'),
            step3_title=request.form.get('step3_title'),
            step3_desc=request.form.get('step3_desc'),
            image_url=image,
            is_active=bool(request.form.get('is_active'))
        )
        db.session.add(defi)
        db.session.commit()
        flash('Défi créé ✦', 'success')
        return redirect(url_for('admin.defis'))
    return render_template('admin/defi_form.html', item=None)

@admin_bp.route('/defis/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def defi_edit(id):
    defi = Defi.query.get_or_404(id)
    if request.method == 'POST':
        defi.title       = request.form.get('title')
        defi.description = request.form.get('description')
        defi.step1_title = request.form.get('step1_title')
        defi.step1_desc  = request.form.get('step1_desc')
        defi.step2_title = request.form.get('step2_title')
        defi.step2_desc  = request.form.get('step2_desc')
        defi.step3_title = request.form.get('step3_title')
        defi.step3_desc  = request.form.get('step3_desc')
        defi.is_active   = bool(request.form.get('is_active'))

        image_file = request.files.get('image_url')
        if image_file and image_file.filename:
            defi.image_url = save_image(image_file)
        elif request.form.get('image_url_text'):
            defi.image_url = request.form.get('image_url_text')

        db.session.commit()
        flash('Défi mis à jour ✦', 'success')
        return redirect(url_for('admin.defis'))
    return render_template('admin/defi_form.html', item=defi)

@admin_bp.route('/defis/<int:id>/delete', methods=['POST'])
@admin_required
def defi_delete(id):
    defi = Defi.query.get_or_404(id)
    db.session.delete(defi)
    db.session.commit()
    flash('Défi supprimé.', 'info')
    return redirect(url_for('admin.defis'))

# ── SOLIDARITÉ ──
@admin_bp.route('/solidarite')
@admin_required
def solidarite():
    items = SolidariteAction.query.order_by(SolidariteAction.created_at.desc()).all()
    return render_template('admin/solidarite.html', items=items)

@admin_bp.route('/solidarite/new', methods=['GET', 'POST'])
@admin_required
def solidarite_new():
    if request.method == 'POST':
        image_file = request.files.get('image_url')
        image = save_image(image_file) or request.form.get('image_url_text')

        action = SolidariteAction(
            title=request.form.get('title'),
            description=request.form.get('description'),
            progress=int(request.form.get('progress', 0)),
            icon_type=request.form.get('icon_type', 'light'),
            image_url=image,
            is_featured=bool(request.form.get('is_featured')),
            is_active=bool(request.form.get('is_active'))
        )
        db.session.add(action)
        db.session.commit()
        flash('Action de solidarité créée ✦', 'success')
        return redirect(url_for('admin.solidarite'))
    return render_template('admin/solidarite_form.html', item=None)

@admin_bp.route('/solidarite/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def solidarite_edit(id):
    action = SolidariteAction.query.get_or_404(id)
    if request.method == 'POST':
        action.title       = request.form.get('title')
        action.description = request.form.get('description')
        action.progress    = int(request.form.get('progress', 0))
        action.icon_type   = request.form.get('icon_type', 'light')
        action.is_featured = bool(request.form.get('is_featured'))
        action.is_active   = bool(request.form.get('is_active'))

        image_file = request.files.get('image_url')
        if image_file and image_file.filename:
            action.image_url = save_image(image_file)
        elif request.form.get('image_url_text'):
            action.image_url = request.form.get('image_url_text')

        db.session.commit()
        flash('Action mise à jour ✦', 'success')
        return redirect(url_for('admin.solidarite'))
    return render_template('admin/solidarite_form.html', item=action)

@admin_bp.route('/solidarite/<int:id>/delete', methods=['POST'])
@admin_required
def solidarite_delete(id):
    action = SolidariteAction.query.get_or_404(id)
    db.session.delete(action)
    db.session.commit()
    flash('Action supprimée.', 'info')
    return redirect(url_for('admin.solidarite'))

# ── FORUM ──
@admin_bp.route('/forum')
@admin_required
def forum():
    items = ForumTopic.query.order_by(ForumTopic.created_at.desc()).all()
    return render_template('admin/forum.html', items=items)

@admin_bp.route('/forum/new', methods=['GET', 'POST'])
@admin_required
def forum_new():
    if request.method == 'POST':
        topic = ForumTopic(
            title=request.form.get('title'),
            excerpt=request.form.get('excerpt'),
            category=request.form.get('category'),
            author_name=request.form.get('author_name'),
            is_pinned=bool(request.form.get('is_pinned')),
            is_hot=bool(request.form.get('is_hot')),
            reply_count=int(request.form.get('reply_count', 0)),
            is_visible=bool(request.form.get('is_visible'))
        )
        db.session.add(topic)
        db.session.commit()
        flash('Sujet créé ✦', 'success')
        return redirect(url_for('admin.forum'))
    return render_template('admin/forum_form.html', item=None)

@admin_bp.route('/forum/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def forum_edit(id):
    topic = ForumTopic.query.get_or_404(id)
    if request.method == 'POST':
        topic.title       = request.form.get('title')
        topic.excerpt     = request.form.get('excerpt')
        topic.category    = request.form.get('category')
        topic.author_name = request.form.get('author_name')
        topic.is_pinned   = bool(request.form.get('is_pinned'))
        topic.is_hot      = bool(request.form.get('is_hot'))
        topic.reply_count = int(request.form.get('reply_count', 0))
        topic.is_visible  = bool(request.form.get('is_visible'))
        db.session.commit()
        flash('Sujet mis à jour ✦', 'success')
        return redirect(url_for('admin.forum'))
    return render_template('admin/forum_form.html', item=topic)

@admin_bp.route('/forum/<int:id>/delete', methods=['POST'])
@admin_required
def forum_delete(id):
    topic = ForumTopic.query.get_or_404(id)
    db.session.delete(topic)
    db.session.commit()
    flash('Sujet supprimé.', 'info')
    return redirect(url_for('admin.forum'))

# ── NEWSLETTER ──
@admin_bp.route('/newsletter')
@admin_required
def newsletter():
    items = Newsletter.query.order_by(Newsletter.created_at.desc()).all()
    active_count = Newsletter.query.filter_by(is_active=True).count()
    return render_template('admin/newsletter.html', items=items, active_count=active_count)

@admin_bp.route('/newsletter/<int:id>/toggle', methods=['POST'])
@admin_required
def newsletter_toggle(id):
    sub = Newsletter.query.get_or_404(id)
    sub.is_active = not sub.is_active
    db.session.commit()
    return redirect(url_for('admin.newsletter'))

@admin_bp.route('/newsletter/<int:id>/delete', methods=['POST'])
@admin_required
def newsletter_delete(id):
    sub = Newsletter.query.get_or_404(id)
    db.session.delete(sub)
    db.session.commit()
    flash('Abonné supprimé.', 'info')
    return redirect(url_for('admin.newsletter'))
