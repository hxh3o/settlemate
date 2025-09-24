import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import { API } from '../api';
import { Typography } from '@mui/material';

function Login() {
	let navigate = useNavigate();

	const [creds, setcreds] = useState({ email: '', password: '' });
	const onChange = event => {
		setcreds({ ...creds, [event.target.name]: event.target.value });
	};
	useEffect(() => {
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			if (authToken) navigate('/');
		}
		authorize();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const handleSubmit = async e => {
		e.preventDefault();
        const response = await fetch(`${API}/forgotPassword`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				email: creds.email,
			}),
		});
		const json = await response.json();
		if (!json.success) {
			json.errors.forEach(error => {
				toast.error(error.msg, {});
			});
		} else {
			localStorage.setItem('reset', true);
			navigate('/');
		}
	};

	return (
		<div style={{ width: '100%', height: '100%' }}>
			<form
				onSubmit={handleSubmit}
				style={{
					display: 'flex',
					flexDirection: 'column',
					justifyContent: 'center',
					alignItems: 'center',
					width: '100%',
					height: '100%',
				}}
			>
				<Typography
					label='Email'
					variant='h5'
					type='text'
					id='email'
					name='email'
					value={creds.email}
					onChange={onChange}
					style={{ textAlign: 'center', width: '27%' }}
				>
					RESET PASSWORD LINK
				</Typography>
				<TextField
					label='Email'
					variant='outlined'
					type='text'
					id='email'
					name='email'
					value={creds.email}
					onChange={onChange}
					style={{ marginTop: '20px', width: '27%' }}
				></TextField>
				<Button
					variant='contained'
					type='submit'
					style={{
						marginTop: '20px',
						width: '27%',
						height: '56px',
						gap: '5%',
					}}
				>
					Forgot Password
				</Button>
				<div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center', width: '27%', height: '56px', gap: '5%' }}>
					<Button variant='outlined' onClick={() => navigate('/login')} style={{ width: '50%', height: '100%' }}>
						Login
					</Button>
					<Button variant='outlined' onClick={() => navigate('/signup')} style={{ width: '50%', height: '100%' }}>
						Sign Up
					</Button>
				</div>
			</form>
		</div>
	);
}

export default Login;
