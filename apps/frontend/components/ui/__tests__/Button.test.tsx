import { render, screen } from '@testing-library/react'

import { Button } from '../Button'

describe('Button', () => {
  it('renders the provided label', () => {
    render(<Button>Bid now</Button>)

    expect(screen.getByRole('button', { name: 'Bid now' })).toBeInTheDocument()
  })

  it('applies the selected variant and size classes', () => {
    render(
      <Button variant="secondary" size="lg">
        Secondary
      </Button>
    )

    const button = screen.getByRole('button', { name: 'Secondary' })

    expect(button).toHaveClass('bg-purple-500/20')
    expect(button).toHaveClass('h-12')
  })
})
