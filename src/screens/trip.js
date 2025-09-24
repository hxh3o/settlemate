import { useState, useEffect, useRef, Fragment } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import MemberTable from './membertable';
import { API, authHeaders } from '../api';
// Socket.IO removed (disabled)
// Removed image upload feature

import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Modal from '@mui/material/Modal';
import Box from '@mui/material/Box';

const style = {
	position: 'absolute',
	top: '50%',
	left: '50%',
	transform: 'translate(-50%, -50%)',
	width: 'auto',
	maxWidth: '50%',
	height: 'auto',
	maxHeight: '50%',
	bgcolor: 'background.paper',
	border: '2px solid #000',
	boxShadow: 24,
	p: 4,
	display: 'flex',
	justifyContent: 'center',
	alignItems: 'center',
	flexDirection: 'column',
};
// Removed image modal styles

const basestyle = {
	flex: 1,
	display: 'flex',
	flexDirection: 'column',
	alignItems: 'center',
	padding: '20px',
	borderWidth: 2,
	borderRadius: 2,
	borderColor: '#eeeeee',
	borderStyle: 'dashed',
	backgroundColor: '#fafafa',
	color: '#bdbdbd',
	outline: 'none',
	transition: 'border .24s ease-in-out',
};

// Removed dropzone thumb styles

function Trip() {
	let navigate = useNavigate();
	const location = useLocation();
    // Socket disabled
	const { tripid } = location.state || {};
	const [data, setData] = useState({ owner: {} });
	const [chat, setChat] = useState([]);
	const [mapId2Name, setMapId2Name] = useState({});
	const [myUid, setMyUid] = useState(null);
	const [msgText, setMsgText] = useState('');
	const [inviteEmail, setInviteEmail] = useState('');
	const [dense, setDense] = useState(false);
    // Removed image state
	const [isButtonDisabled, setIsButtonDisabled] = useState(false);

	const [clearChatOpen, setClearChatModalOpen] = useState(false);
    const [fileOpen, setfileModalOpen] = useState(false);
	const [inviteOpen, setInviteModal] = useState(false);

	const chatEndRef = useRef(null);
	useEffect(() => {
		chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	}, [chat]);

    // Removed dropzone hook and previews

	useEffect(() => {
		// Guard against missing/invalid tripid early
		if (!tripid || typeof tripid !== 'string' || tripid.length < 10) {
			navigate('/');
			return;
		}
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			// console.log(authToken)
			if (!authToken) navigate('/');
			else {
				fetchData();
			}
		}
		async function fetchData() {
			try {
                const response = await fetch(`${API}/getTripData`, {
					method: 'POST',
                    headers: authHeaders(),
					body: JSON.stringify({
						tripid: tripid,
					}),
				});
				const json = await response.json();
				if (json.success) {
					setData(json.data);
					setMyUid(json.userId);
					setMapId2Name(json.mapId2Name);
					setChat(json.chat);
					// console.log(json.chat);
					// console.log(data);
				} else {
					json.errors.forEach(error => {
						toast.error(error.msg, {});
					});
					if (json.logout === true) {
						localStorage.removeItem('authToken');
						localStorage.setItem('forcedLogOut', true);
						navigate('/profile');
					}
				}
			} catch (error) {
				console.error('Error fetching trip Data :', error);
			}
		}
		authorize();
        return () => {};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

// Socket disabled

	const msgTextSubmit = async e => {
		if (!Array.isArray(e)) e.preventDefault();
		if (msgText.length === 0 && !Array.isArray(e)) {
			toast.error('Cannot Send Empty message');
			return;
		}
        const data = {
			msg: !Array.isArray(e) ? msgText : e[0],
            isImage: false,
			from: myUid,
			date: new Date(),
		};
        // Socket disabled; rely on HTTP addChat and local append
        const response = await fetch(`${API}/addChat`, {
			method: 'POST',
            headers: authHeaders(),
			body: JSON.stringify({
				tripid: tripid,
				msg: data,
			}),
		});
		const json = await response.json();
		if (!json.success) {
			json.errors.forEach(error => {
				toast.error(error.msg, {});
			});
			if (json.logout === true) {
				localStorage.removeItem('authToken');
				localStorage.setItem('forcedLogOut', true);
				navigate('/profile');
			}
		} else {
			// Optimistically append to chat if server confirms addChat
			setChat(prev => [
				...prev,
				{
					from: myUid,
					msg: data.msg,
					isImage: data.isImage,
					date: new Date().toISOString(),
				},
			]);
			if (!Array.isArray(e)) setMsgText('');
		}
	};
	const clearChat = async () => {
		if (myUid === data.owner.id) setClearChatModalOpen(true);
		else msgTextSubmit('Admin please clear the chat!');
	};
	const confirmClearChat = async () => {
        const response = await fetch(`${API}/clearChat`, {
			method: 'POST',
            headers: authHeaders(),
			body: JSON.stringify({
				tripid: tripid,
			}),
		});
		const json = await response.json();
		console.log(json);
		if (!json.success) {
			json.errors.forEach(error => {
				toast.error(error.msg, {});
			});
			if (json.logout === true) {
				localStorage.removeItem('authToken');
				localStorage.setItem('forcedLogOut', true);
				navigate('/profile');
			}
		} else {
			setClearChatModalOpen(false);
			msgTextSubmit(['Admin cleared the chat!', false]);
		}
	};
    // Removed uploadImages function

	const sendInvite = async () => {
        const response = await fetch(`${API}/invite`, {
			method: 'POST',
            headers: authHeaders(),
			body: JSON.stringify({
				tripid: tripid,
				email: inviteEmail,
			}),
		});
		const json = await response.json();
		if (!json.success) {
			(json.errors || []).forEach(error => {
				toast.error(error.msg, {});
			});
			if (json.logout === true) {
				localStorage.removeItem('authToken');
				localStorage.setItem('forcedLogOut', true);
				navigate('/profile');
			}
		} else {
			setInviteModal(false);
			setInviteEmail('');
			toast.success(json.message || 'Invite sent!', {});
		}
	};

	return (
		<div style={{ overflow: 'hidden', height: '100%' }}>
            {/* Removed image upload modal */}
			<Modal
				open={clearChatOpen}
				onClose={() => {
					setClearChatModalOpen(false);
				}}
				aria-labelledby='modal-modal-titleclearChat'
				aria-describedby='modal-modal-descriptionclearChat'
			>
				<Box sx={style}>
					<Typography id='modal-modal-titleclearChat' variant='h6' component='h2' style={{ textAlign: 'center' }}>
						Irrversible Action
					</Typography>
					<Button id='modal-modal-descriptionclearChat' sx={{ mt: 2 }} variant='contained' onClick={confirmClearChat}>
						Confirm Clear Chat
					</Button>
				</Box>
			</Modal>
            {/* Removed image preview modal */}
			<Modal
				open={inviteOpen}
				onClose={() => {
					setInviteModal(false);
				}}
				aria-labelledby='modal-modal-titleinvite'
				aria-describedby='modal-modal-descriptioninvite'
			>
				<Box sx={style}>
					<TextField
						type='text'
						id='text'
						value={inviteEmail}
						label='Account Email'
						onChange={e => setInviteEmail(e.target.value)}
						style={{ width: '30vw' }}
						variant='outlined'
						autoComplete='off'
					/>
					<Button id='modal-modal-descriptioninvite' sx={{ mt: 2 }} variant='contained' onClick={sendInvite}>
						Send Invite
					</Button>
				</Box>
			</Modal>
			<div
				style={{
					display: 'grid',
					gridTemplateColumns: '49.7% 0.6% 49.7%',
					height: '100%',
				}}
			>
				<div style={{ overflow: 'hidden', height: '100%' }}>
					<div style={{ height: '35%' }}>
						<Typography
							variant='h2'
							gutterBottom
							style={{
								marginLeft: '10px',
								color: '#1976D2',
								textAlign: 'center',
							}}
						>
							{data.name}
						</Typography>
						<Typography
							variant='h4'
							gutterBottom
							style={{
								marginLeft: '10px',
								color: '#1976D2',
								textAlign: 'center',
							}}
						>
							Managed By : {data.owner.name}
						</Typography>
						<div
							style={{
								display: 'flex',
								justifyContent: 'space-evenly',
								gap: '10px',
							}}
						>
							<Button
								variant='contained'
								onClick={() =>
									navigate('/transactions', {
										state: { tripid: tripid },
									})
								}
							>
								Transactions
							</Button>
							<Button
								variant='contained'
								onClick={() =>
									navigate('/transfer', {
										state: { tripid: tripid },
									})
								}
							>
								Minimum Transfers
							</Button>
						{myUid === data.owner.id && (
								<Button
									variant='contained'
									onClick={() => {
										setInviteModal(true);
									}}
								>
									Invite Members
								</Button>
							)}
						{myUid === data.owner.id && (
								<Button
									variant='contained'
									onClick={() =>
										navigate('/edittrip', {
											state: { tripid: tripid },
										})
									}
								>
									Edit Trip
								</Button>
							)}
						</div>
					</div>
					<div style={{ overflowY: 'scroll', height: '65%' }}>
						<MemberTable tripid={tripid} />
					</div>
				</div>
				<div style={{ backgroundColor: '#1976D2', height: '100%' }}></div>
				<div style={{ maxHeight: '93vh' }}>
					<div style={{ height: '80%', overflow: 'scroll' }}>
						<List dense={dense}>
							{chat.map((chat, index) => (
								<ListItem key={index}>
									<ListItemText
										align={chat.from === myUid ? 'right' : 'left'}
										primary={
											<Fragment>
								{chat.msg}
											</Fragment>
										}
										secondary={`${mapId2Name[chat.from]} - ${new Date(chat.date).toLocaleDateString()} ${new Date(
											chat.date
										).toLocaleTimeString()}`}
										sx={{ whiteSpace: 'normal' }}
									/>
								</ListItem>
							))}
							<div ref={chatEndRef} />
						</List>
					</div>
					<form
						onSubmit={msgTextSubmit}
						style={{
							display: 'grid',
							gridTemplateColumns: '80% 20%',
							height: '10%',
						}}
					>
						<div
							style={{
								height: 'auto',
								width: '100%',
								paddingLeft: '10px',
							}}
						>
							<TextField
								type='text'
								id='text'
								value={msgText}
								label='Message'
								onChange={e => setMsgText(e.target.value)}
								style={{ width: '100%' }}
								variant='standard'
								autoComplete='off'
							/>
						</div>
						<div>
							<div
								style={{
									display: 'flex',
									justifyContent: 'center',
									alignItems: 'center',
									paddingTop: '10px',
								}}
							>
								<Button variant='contained' type='submit'>
									Send Text
								</Button>
							</div>
						</div>
					</form>
					<div
						style={{
							height: '10%',
							display: 'grid',
							gridTemplateColumns: '33% 33% 33%',
						}}
					>
						<div
							style={{
								display: 'flex',
								justifyContent: 'center',
								alignItems: 'center',
							}}
						>
                            {/* Removed Upload Image button */}
						</div>
						<div
							style={{
								display: 'flex',
								justifyContent: 'center',
								alignItems: 'center',
							}}
						>
							<Button variant='contained' onClick={clearChat}>
								Clear Chat
							</Button>
						</div>
						<div
							style={{
								display: 'flex',
								justifyContent: 'center',
								alignItems: 'center',
							}}
						>
							<Button
								variant='contained'
								onClick={() => {
									setDense(!dense);
								}}
							>
								Toggle Density
							</Button>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}

export default Trip;
