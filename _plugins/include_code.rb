module Jekyll
  class IncludeCodeTag < Liquid::Tag
    def initialize(tag_name, markup, tokens)
      super
      @params = {}
      markup.scan(/(\w+)="([^"]+)"/) do |key, value|
        @params[key] = value
      end
      @start_line = (@params["start"] ? @params["start"].to_i : nil)
      @end_line   = (@params["end"] ? @params["end"].to_i : nil)
      @file_path  = @params["file"]
      @lang       = @params["lang"] || ""
    end

    def render(context)
      site = context.registers[:site]
      full_path = File.join(site.source, @file_path)

      unless File.exist?(full_path)
        return "Error: File '#{@file_path}' not found."
      end

      code = File.read(full_path)
      code_lines = code.split("\n")

      if @start_line && @end_line
        # Adjust for zero-indexed arrays; slice is end-exclusive.
        selected_lines = code_lines[(@start_line - 1)...@end_line]
      else
        selected_lines = code_lines
      end

      code_block = selected_lines.join("\n")

      # Return the code block with proper Markdown formatting.
      <<~MARKDOWN
      ```#{@lang}
      #{code_block}
      ```
      MARKDOWN
    end
  end
end

Liquid::Template.register_tag('include_code', Jekyll::IncludeCodeTag)
