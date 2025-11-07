# ChukMCPServer Documentation

This directory contains the MDX-based documentation for ChukMCPServer, designed for deployment with documentation platforms like Mintlify, Docusaurus, or Nextra.

## Structure

```
docs/
├── getting-started/
│   ├── welcome.mdx          # Welcome page with overview
│   ├── installation.mdx     # Installation guide
│   ├── quickstart.mdx       # 5-minute quickstart
│   └── core-concepts.mdx    # Core MCP concepts
│
├── deployment/
│   ├── running-server.mdx   # Running servers locally
│   ├── docker.mdx           # Docker deployment
│   ├── cloud.mdx            # Cloud platforms
│   └── configuration.mdx    # Configuration reference
│
├── servers/
│   ├── composition.mdx      # Server composition
│   ├── proxy.mdx            # Proxy servers
│   └── multi-server.mdx     # Multi-server patterns
│
├── advanced/
│   ├── oauth.mdx            # OAuth 2.1 integration
│   ├── performance.mdx      # Performance optimization
│   └── security.mdx         # Security best practices
│
└── api-reference/
    ├── decorators.mdx       # @tool, @resource, @prompt
    ├── server.mdx           # ChukMCPServer class
    └── types.mdx            # Type system

```

## Documentation Platform

These MDX files are designed to work with popular documentation platforms:

### Mintlify (Recommended)
- Modern, fast, and beautiful
- Excellent component library
- AI-friendly features
- Similar to FastMCP's docs

### Alternative Platforms
- **Docusaurus** - Popular open-source option
- **Nextra** - Next.js-based docs
- **GitBook** - Simple and clean
- **MkDocs Material** - Python-friendly

## Local Development

### Using Mintlify

```bash
# Install Mintlify CLI
npm install -g mintlify

# Start dev server
cd /path/to/chuk-mcp-server
mintlify dev

# Preview at http://localhost:3000
```

### Using Docusaurus

```bash
# Install Docusaurus
npx create-docusaurus@latest docs-site classic

# Copy MDX files to docs/
cp -r docs/* docs-site/docs/

# Start dev server
cd docs-site && npm start
```

## MDX Components

The documentation uses standard MDX components that work across platforms:

- `<Card>` - Feature cards
- `<CardGroup>` - Grid layout for cards
- `<Accordion>` - Collapsible content
- `<AccordionGroup>` - Multiple accordions
- `<Tabs>` - Tabbed content
- `<Steps>` - Step-by-step guides
- `<Info>` - Info callouts
- `<Warning>` - Warning callouts
- `<Check>` - Success callouts

## Contributing to Docs

### Guidelines

1. **Clear and Concise** - Get to the point quickly
2. **Code Examples** - Include runnable code in every guide
3. **Progressive Disclosure** - Basic → Advanced
4. **Search Optimization** - Use clear headings and keywords
5. **AI-Friendly** - Structure for both humans and LLMs

### Adding a New Page

1. Create MDX file in appropriate directory
2. Add frontmatter with title, description, icon
3. Update `mint.json` navigation
4. Test locally before committing

### Frontmatter Template

```mdx
---
title: "Your Page Title"
sidebarTitle: "Short Title"
description: "One-line description for SEO and AI"
icon: "icon-name"
---
```

## Icons

Use FontAwesome icon names without the `fa-` prefix:
- `rocket-launch`, `cloud`, `shield-check`, `puzzle-piece`
- `code`, `book`, `bolt`, `download`, `hand-wave`

Full list: https://fontawesome.com/icons

## Deployment

### GitHub Pages

```bash
# Build static site
mintlify build

# Deploy to GitHub Pages
gh-pages -d build
```

### Vercel

```bash
# Deploy with Vercel
vercel deploy
```

### Netlify

```bash
# Deploy with Netlify
netlify deploy --prod
```

## TODO

- [ ] Complete all core documentation pages
- [ ] Add more code examples
- [ ] Create video tutorials
- [ ] Add interactive demos
- [ ] Set up search indexing
- [ ] Add changelog/release notes
- [ ] Create API reference from docstrings

## Resources

- [Mintlify Documentation](https://mintlify.com/docs)
- [MDX Documentation](https://mdxjs.com/)
- [FastMCP Docs](https://gofastmcp.com/) (inspiration)
- [MCP Specification](https://modelcontextprotocol.io/)
