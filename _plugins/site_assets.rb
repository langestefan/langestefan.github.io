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

  module_function

  # Absolute-from-root URL that respects site.baseurl.
  def asset_url(site, path)
    baseurl = site.config["baseurl"].to_s.chomp("/")
    "#{baseurl}/#{path}"
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
    end

    tags.join("\n")
  end

  def inject(site, item)
    output = item.output
    return unless output.is_a?(String)
    return unless output.include?("</head>") || output.include?("</body>")
    # Idempotent: a page rendered twice must not get two copies.
    return if output.include?(CSS)

    output = output.sub("</head>", "#{head_tags(site)}\n</head>") if output.include?("</head>")
    output = output.sub(%r{</body>}, "#{body_tags(site, item)}\n</body>") if output.include?("</body>")
    item.output = output
  end
end

Jekyll::Hooks.register :documents, :post_render do |doc|
  SiteAssets.inject(doc.site, doc)
end

Jekyll::Hooks.register :pages, :post_render do |page|
  SiteAssets.inject(page.site, page)
end
