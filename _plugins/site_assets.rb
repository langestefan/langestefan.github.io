require "cgi"
require "digest"

# Injects this site's own stylesheet and scripts into every rendered page.
#
# Why a plugin instead of overriding _includes/head.liquid and
# _includes/scripts.liquid: in al-folio v1 those files are owned by
# al_folio_core, and the Distill layout does not use them at all -- it is
# rendered by the al_folio_distill_render tag from a template inside the gem.
# Shadowing them would mean carrying hundreds of lines of gem-owned Liquid
# forever and re-reviewing it on every `bundle update`, all to add three tags.
#
# A post_render hook reaches every layout uniformly (page, post and distill)
# and touches nothing the gems own.
module SiteAssets
  CSS = "assets/css/custom.css".freeze
  HEADING_ANCHORS_JS = "assets/js/heading-anchors.js".freeze
  DISTILL_BUTTON_JS = "assets/js/distill-github-button.js".freeze
  SIDENOTES_JS = "assets/js/sidenotes.js".freeze

  module_function

  # Absolute-from-root URL that respects site.baseurl, with a content hash so a
  # changed asset is actually re-fetched. Without this a browser holds the old
  # copy indefinitely: the gems' own assets all ship "?v=<md5>", and these were
  # the only stylesheets and scripts on the page without it.
  def asset_url(site, path)
    baseurl = site.config["baseurl"].to_s.chomp("/")
    "#{baseurl}/#{path}?v=#{digest(site, path)}"
  end

  # Digest of the file that produces `path`. assets/css/custom.css is generated
  # from custom.scss, so the source is hashed rather than the build output,
  # which does not exist in site.source.
  def digest(site, path)
    source = File.join(site.source, path)
    source = source.sub(/\.css\z/, ".scss") if !File.exist?(source) && path.end_with?(".css")
    return "0" unless File.exist?(source)

    key = [source, File.mtime(source).to_i]
    @digests ||= {}
    @digests[key] ||= Digest::MD5.file(source).hexdigest[0, 16]
  end

  # Repository slug used to build "view source" links, e.g.
  # "langestefan/langestefan.github.io".
  def repo_slug(site)
    giscus = site.config["giscus"]
    giscus.is_a?(Hash) ? giscus["repo"] : nil
  end

  def distill?(page_or_doc)
    layout = page_or_doc.data["layout"]
    layout.to_s == "distill"
  end

  # Path of the source file within the repository, for the GitHub link.
  def source_path(item)
    return item.relative_path.to_s.sub(%r{\A/}, "") if item.respond_to?(:relative_path) && item.relative_path
    return item.path.to_s.sub(%r{\A/}, "") if item.respond_to?(:path) && item.path

    nil
  end

  def head_tags(site)
    %(<link rel="stylesheet" href="#{asset_url(site, CSS)}">)
  end

  def body_tags(site, item)
    tags = [%(<script defer src="#{asset_url(site, HEADING_ANCHORS_JS)}"></script>)]

    if distill?(item)
      slug = repo_slug(site)
      path = source_path(item)
      if slug && path
        url = "https://github.com/#{slug}/blob/main/#{path}"
        tags << %(<script>window.__alGithubSourceUrl = "#{url}";</script>)
      end
      tags << %(<script defer src="#{asset_url(site, DISTILL_BUTTON_JS)}"></script>)
      tags << %(<script defer src="#{asset_url(site, SIDENOTES_JS)}"></script>)
    end

    tags.join("\n")
  end

  # "Cite this as" block for Distill posts.
  #
  # al_folio_core's post.liquid honours `citation: true`, but the Distill
  # render template in al_folio_distill does not, so a distill post with
  # citation: true silently renders no citation. This site's v0 theme patched
  # the distill layout to include it; that layout no longer exists, so the
  # block is built here and injected into <d-appendix> instead.
  #
  # The two lead-in sentences the stock include emits ("If you found this
  # useful..." / "or as a BibTeX entry:") are intentionally omitted, matching
  # the wording this site has used since 2025.
  def citation_html(site, item)
    cfg = site.config
    first = cfg["first_name"].to_s
    middle = cfg["middle_name"].to_s
    last = cfg["last_name"].to_s
    title = item.data["title"].to_s
    date = item.data["date"]
    return nil unless date.respond_to?(:strftime)

    author = middle.empty? ? "#{last}, #{first}" : "#{last}, #{first} #{middle}"
    site_title = cfg["title"].to_s
    journal = (site_title.empty? || site_title == "blank") ? nil : site_title
    url = "#{cfg["url"]}#{item.url}"

    quote = +"#{author} (#{date.strftime("%b %Y")}). #{title}."
    quote << " #{journal}." if journal
    quote << " #{cfg["url"]}."

    key = "#{last.downcase}#{date.strftime("%Y")}#{Jekyll::Utils.slugify(title)}"
    bibtex = +"@article{#{key},\n"
    bibtex << "  title   = {#{title}},\n"
    bibtex << "  author  = {#{author}},\n"
    bibtex << "  journal = {#{journal}},\n" if journal
    bibtex << "  year    = {#{date.strftime("%Y")}},\n"
    bibtex << "  month   = {#{date.strftime("%b")}},\n"
    bibtex << "  url     = {#{url}}\n}"

    <<~HTML
      <br>
      <hr>
      <br>
      <blockquote><p>#{CGI.escapeHTML(quote)}</p></blockquote>
      <div class="language-bibtex highlighter-rouge"><div class="highlight"><pre class="highlight"><code>#{CGI.escapeHTML(bibtex)}</code></pre></div></div>
    HTML
  end

  def inject_citation(site, item, output)
    return output unless distill?(item)
    return output unless item.data["citation"]
    return output unless output.include?("</d-appendix>")
    return output if output.include?("language-bibtex")

    html = citation_html(site, item)
    return output unless html

    output.sub("</d-appendix>", "#{html}</d-appendix>")
  end

  def inject(site, item)
    output = item.output
    return unless output.is_a?(String)
    return unless output.include?("</head>") || output.include?("</body>")
    # Idempotent: a page rendered twice must not get two copies.
    return if output.include?(CSS)

    output = output.sub("</head>", "#{head_tags(site)}\n</head>") if output.include?("</head>")
    output = output.sub(%r{</body>}, "#{body_tags(site, item)}\n</body>") if output.include?("</body>")
    output = inject_citation(site, item, output)
    item.output = output
  end
end

Jekyll::Hooks.register :documents, :post_render do |doc|
  SiteAssets.inject(doc.site, doc)
end

Jekyll::Hooks.register :pages, :post_render do |page|
  SiteAssets.inject(page.site, page)
end
