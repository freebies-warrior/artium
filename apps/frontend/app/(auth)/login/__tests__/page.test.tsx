import type { ImgHTMLAttributes } from 'react'

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import LoginPage from '../page'

const replaceMock = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: replaceMock,
  }),
}))

vi.mock('next/image', () => ({
  default: (props: ImgHTMLAttributes<HTMLImageElement>) => (
    <img alt={props.alt} {...props} />
  ),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    replaceMock.mockReset()
    vi.restoreAllMocks()
  })

  it('renders login form fields', () => {
    render(<LoginPage />)

    expect(
      screen.getByRole('heading', { level: 1, name: 'Login' })
    ).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Email Address')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument()
  })

  it('submits credentials and redirects on success', async () => {
    const user = userEvent.setup()

    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    } as Response)

    render(<LoginPage />)

    await user.type(screen.getByPlaceholderText('Email Address'), 'me@test.io')
    await user.type(screen.getByPlaceholderText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Login' }))

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'me@test.io', password: 'password123' }),
      })
      expect(replaceMock).toHaveBeenCalledWith('/')
    })
  })
})
