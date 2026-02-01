import type { ImgHTMLAttributes } from 'react'

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import SignupPage from '../page'

vi.mock('next/image', () => ({
  default: (props: ImgHTMLAttributes<HTMLImageElement>) => (
    <img alt={props.alt} {...props} />
  ),
}))

describe('SignupPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('shows a validation error when passwords do not match', async () => {
    const user = userEvent.setup()

    const fetchSpy = vi.spyOn(global, 'fetch')

    render(<SignupPage />)

    await user.type(screen.getByPlaceholderText('Username'), 'artist')
    await user.type(screen.getByPlaceholderText('Email Address'), 'me@test.io')
    await user.type(screen.getByPlaceholderText('Password'), 'pass1')
    await user.type(screen.getByPlaceholderText('Confirm Password'), 'pass2')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(
      await screen.findByText('Passwords do not match')
    ).toBeInTheDocument()
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('shows a success message after signup', async () => {
    const user = userEvent.setup()

    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    } as Response)

    render(<SignupPage />)

    await user.type(screen.getByPlaceholderText('Username'), 'artist')
    await user.type(screen.getByPlaceholderText('Email Address'), 'me@test.io')
    await user.type(screen.getByPlaceholderText('Password'), 'pass1234')
    await user.type(screen.getByPlaceholderText('Confirm Password'), 'pass1234')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'artist',
          email: 'me@test.io',
          password: 'pass1234',
        }),
      })
    })

    expect(
      await screen.findByText(
        'Account created! Please check your email to verify your account.'
      )
    ).toBeInTheDocument()
  })
})
