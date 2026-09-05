# {% sidenote %} ... {% endsidenote %}
#
# Writes a Tufte-style margin note without any HTML in the post:
#
#     Some claim in the prose.{% sidenote %}The qualifying **detail**.{% endsidenote %}
#
# The tag emits only inline markup at the point of use: a marker, and the note
# body in a hidden sibling span. assets/js/sidenotes.js then lifts the body into
# a real <aside> placed directly after the marker's top-level block.
#
# It has to work this way round. Distill positions a sidenote with
# `grid-column: gutter`, which only applies to direct children of <d-article>,
# so an <aside> emitted inline -- inside the paragraph or list item being
# annotated -- would never reach the margin. The body is reduced to span-level
# HTML before being emitted, because kramdown escapes raw block tags appearing
# in an inline context and a <p> would otherwise arrive as literal &lt;p&gt;.
module Jekyll
  class SidenoteTag < Liquid::Block
    def render(context)
      site = context.registers[:site]
      converter = site.find_converter_instance(::Jekyll::Converters::Markdown)
      html = converter.convert(super.strip).strip

      # Reduce the rendered markdown to span-level HTML. Kramdown escapes raw
      # block tags that appear in an inline context -- and this tag is used
      # mid-sentence -- so a <p> here comes back as &lt;p&gt; and the note would
      # render as literal angle brackets. Paragraph breaks become <br><br>;
      # margin notes are short and do not need block structure.
      html = html.gsub(%r{</p>\s*<p[^>]*>}, "<br><br>")
      html = html.sub(%r{\A<p[^>]*>}, "").sub(%r{</p>\z}, "")

      %(<span class="sidenote-ref"></span><span class="sidenote-body">#{html}</span>)
    end
  end
end

Liquid::Template.register_tag("sidenote", Jekyll::SidenoteTag)
